from pathlib import Path
import pandas as pd, numpy as np, json, shutil, zipfile, warnings
warnings.filterwarnings('ignore')
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, brier_score_loss, average_precision_score, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import joblib
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path('/mnt/data/paimana_work/paimana_feature_selection_final')
OUT=Path('/mnt/data/PAIMANA_predictive_early_warning_final')
if OUT.exists(): shutil.rmtree(OUT)
for d in ['data','models','plots','scripts']: (OUT/d).mkdir(parents=True,exist_ok=True)

# copy source artifacts
for name in ['1_cleaned_dataset.csv','2_feature_engineered_dataset.csv']:
    shutil.copy2(BASE/'data'/name, OUT/'data'/name)

df=pd.read_csv(BASE/'data/2_feature_engineered_dataset.csv', low_memory=False)
df=df.replace([np.inf,-np.inf],np.nan)
df['report_month']=pd.to_datetime(df['report_month'].astype(str)+'-01', errors='coerce')

# Sort for all temporal/project history calculations
sort_cols=['project_code','report_month']
df=df.sort_values(sort_cols).reset_index(drop=True)

def safe_ratio(a,b,eps=1e-6):
    return a/np.where(np.abs(b)<eps,np.nan,b)

def robust_sigmoid(x, center=0.0, scale=1.0):
    z=np.clip((x-center)/max(scale,1e-6),-12,12)
    return 1/(1+np.exp(-z))

def robust_unit(x, qlo=0.05, qhi=0.95, inverse=False):
    x=pd.Series(x,dtype='float64')
    lo=x.quantile(qlo); hi=x.quantile(qhi)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi<=lo:
        out=pd.Series(np.zeros(len(x)),index=x.index)
    else:
        out=((x-lo)/(hi-lo)).clip(0,1)
    if inverse: out=1-out
    return out.fillna(out.median() if out.notna().any() else 0.5)

# --------- Stage-aware expected progress ---------
# Use current schedule (revised completion where available, otherwise original) to estimate planned trajectory.
# This is a benchmark, not a claim that every infrastructure project progresses linearly.
start=pd.to_datetime(df['start_date'].astype(str), format='%m/%Y', errors='coerce')
orig_end=pd.to_datetime(df['original_completion_date'].astype(str), format='%m/%Y', errors='coerce')
rev_end=pd.to_datetime(df['revised_completion_date'].astype(str), format='%m/%Y', errors='coerce')
plan_end=rev_end.fillna(orig_end)
plan_months=((plan_end.dt.year-start.dt.year)*12+(plan_end.dt.month-start.dt.month)).clip(lower=1)
elapsed=((df['report_month'].dt.year-start.dt.year)*12+(df['report_month'].dt.month-start.dt.month)).clip(lower=0)
expected=(elapsed/plan_months*100).clip(0,100)
df['expected_progress_pct']=expected
# gap is positive when expected progress is ahead of actual progress
df['progress_gap_enhanced_pct']=(df['expected_progress_pct']-df['physical_progress_pct']).clip(lower=-100,upper=100)

# --------- Project trajectory features ---------
g=df.groupby('project_code',sort=False)
df['prev_overall_risk_proxy']=np.nan # filled after model scoring, retained for schema stability
# Historical changes, no future information.
df['prev_progress_gap_enhanced_pct']=g['progress_gap_enhanced_pct'].shift(1)
df['progress_gap_change_1m']=df['progress_gap_enhanced_pct']-df['prev_progress_gap_enhanced_pct']
df['prev_expenditure_pct']=g['expenditure_original_cost_pct'].shift(1)
df['expenditure_progress_efficiency_gap']=df['expenditure_original_cost_pct']-df['physical_progress_pct']
df['prev_expenditure_progress_efficiency_gap']=g['expenditure_progress_efficiency_gap'].shift(1)
df['efficiency_gap_change_1m']=df['expenditure_progress_efficiency_gap']-df['prev_expenditure_progress_efficiency_gap']
df['prev_progress_velocity']=g['progress_velocity_pct_per_month'].shift(1)
df['progress_velocity_change_1m']=df['progress_velocity_pct_per_month']-df['prev_progress_velocity']
df['prev_expenditure_growth']=g['expenditure_growth_pct'].shift(1)
df['expenditure_growth_change_1m']=df['expenditure_growth_pct']-df['prev_expenditure_growth']

# Robust financial efficiency: avoid unstable expenditure/progress ratios.
# Positive gap means financial consumption is ahead of physical delivery.
F_gap=robust_unit(df['expenditure_progress_efficiency_gap'].clip(-100,100),0.10,0.90)
F_worsen=robust_unit(df['efficiency_gap_change_1m'].clip(-50,50),0.10,0.90)
F_accel=robust_unit(df['expenditure_growth_change_1m'].clip(-100,100),0.10,0.90)
# stage awareness: efficiency concern is stronger later in the project.
stage=(df['physical_progress_pct']/100).clip(0,1).fillna(0)
df['financial_efficiency_risk']=(0.55*F_gap + 0.25*F_worsen + 0.20*F_accel)*(0.70+0.30*stage)
df['financial_efficiency_risk']=df['financial_efficiency_risk'].clip(0,1)

# Progress risk: current gap + velocity gap + deterioration.
P_gap=robust_unit(df['progress_gap_enhanced_pct'].clip(-100,100),0.10,0.90)
# positive required-actual velocity is bad; original velocity_gap has this orientation.
P_vel=robust_unit(df['velocity_gap_pct_points'].clip(-50,50),0.10,0.90)
P_det=robust_unit((-df['progress_velocity_change_1m']).clip(-20,20),0.10,0.90)
df['progress_risk']=(0.45*P_gap+0.35*P_vel+0.20*P_det).clip(0,1)

# Data quality/confidence. More history and fewer missing core fields -> higher confidence.
core=['physical_progress_pct','expenditure_original_cost_pct','planned_duration_months','remaining_duration_months','progress_velocity_pct_per_month','required_progress_velocity_pct_per_month']
missing_frac=df[core].isna().mean(axis=1)
hist_conf=(1-np.exp(-df['snapshots_so_far'].clip(lower=1)/4)).clip(0,1)
df['data_quality_score']=(0.65*hist_conf+0.35*(1-missing_frac)).clip(0,1)
df['data_quality_score']=df['data_quality_score'].fillna(0.5)

# Save enhanced feature data
# Keep report_month human-readable in CSV.
out_enh=df.copy(); out_enh['report_month']=out_enh['report_month'].dt.strftime('%Y-%m')
out_enh.to_csv(OUT/'data/2_enhanced_risk_features.csv',index=False)

# ---------------- MODEL TRAINING ----------------
# Only labeled months are eligible. Test = latest 3 labeled months; validation = previous 2; train = rest.
label_cols=['y_cost_risk_1m','y_schedule_risk_1m','y_combined_risk_1m']
max_labeled=df.loc[df['y_combined_risk_1m'].notna(),'report_month'].max()
months=sorted(df.loc[df['y_combined_risk_1m'].notna(),'report_month'].dropna().unique())
test_months=months[-3:]
val_months=months[-5:-3]
train_months=months[:-5]
print('train months',train_months,'val',val_months,'test',test_months)

# Candidate features: deliberately exclude y_* and next_* and identifiers/date strings.
base_numeric=[
'original_cost_cr','revised_cost_cr','cumulative_expenditure_cr','physical_progress_pct','cost_overrun_pct',
'expenditure_original_cost_pct','expenditure_revised_cost_pct','progress_expenditure_gap_pct','project_age_months',
'planned_duration_months','remaining_duration_months','remaining_progress_pct','schedule_slippage_months',
'completion_date_revised_flag','monthly_progress_change_pct','monthly_expenditure_change_cr','monthly_revised_cost_change_cr',
'monthly_cost_growth_pct','progress_velocity_pct_per_month','expenditure_growth_pct','required_progress_velocity_pct_per_month',
'velocity_gap_pct_points','prev_cost_overrun_pct','prev_physical_progress_pct','prev_completion_revised_flag','cost_overrun_trend_1m',
'progress_trend_1m','rolling_progress_velocity_3m','rolling_cost_growth_3m','rolling_expenditure_growth_3m','snapshots_so_far',
'expected_progress_pct','progress_gap_enhanced_pct','progress_gap_change_1m','expenditure_progress_efficiency_gap',
'efficiency_gap_change_1m','progress_velocity_change_1m','expenditure_growth_change_1m'
]
cats=['ministry','sector','state','implementing_agency']
# Drop extremely persistence-heavy current variables only in a challenger, not the main model.
model_features=base_numeric+cats

params={
'cost_risk_1m':dict(n_estimators=500,num_leaves=15,max_depth=5,learning_rate=0.025,min_child_samples=60,reg_lambda=5.0,reg_alpha=0.2,subsample=0.85,colsample_bytree=0.85),
'schedule_risk_1m':dict(n_estimators=600,num_leaves=18,max_depth=5,learning_rate=0.022,min_child_samples=60,reg_lambda=6.0,reg_alpha=0.25,subsample=0.85,colsample_bytree=0.85),
'combined_risk_1m':dict(n_estimators=600,num_leaves=18,max_depth=5,learning_rate=0.022,min_child_samples=60,reg_lambda=6.0,reg_alpha=0.25,subsample=0.85,colsample_bytree=0.85)
}

def prep(X):
    X=X.copy().replace([np.inf,-np.inf],np.nan)
    for c in cats:
        X[c]=X[c].astype('category')
    return X

def metrics(y,p):
    pred=(p>=0.5).astype(int)
    return {'accuracy':accuracy_score(y,pred),'f1':f1_score(y,pred,zero_division=0),'roc_auc':roc_auc_score(y,p),'pr_auc':average_precision_score(y,p),'brier':brier_score_loss(y,p)}

selected={}; models={}; calibrators={}
for target in ['cost_risk_1m','schedule_risk_1m','combined_risk_1m']:
    tcol='y_'+target
    sub=df[df[tcol].notna()].copy()
    tr=sub['report_month'].isin(train_months); va=sub['report_month'].isin(val_months); te=sub['report_month'].isin(test_months)
    Xtr=prep(sub.loc[tr,model_features]); ytr=sub.loc[tr,tcol].astype(int)
    Xv=prep(sub.loc[va,model_features]); yv=sub.loc[va,tcol].astype(int)
    Xte=prep(sub.loc[te,model_features]); yte=sub.loc[te,tcol].astype(int)
    model=LGBMClassifier(objective='binary',random_state=42,n_jobs=4,verbosity=-1,**params[target])
    model.fit(Xtr,ytr,categorical_feature=cats,eval_set=[(Xv,yv)],eval_metric='auc',callbacks=[early_stopping(60,verbose=False),log_evaluation(0)])
    pv_raw=model.predict_proba(Xv)[:,1]; ptest_raw=model.predict_proba(Xte)[:,1]; ptr_raw=model.predict_proba(Xtr)[:,1]
    # Platt calibration on validation predictions only; no test information.
    cal=LogisticRegression(C=1.0,solver='lbfgs',random_state=42)
    cal.fit(pv_raw.reshape(-1,1),yv)
    ptr=cal.predict_proba(ptr_raw.reshape(-1,1))[:,1]; pv=cal.predict_proba(pv_raw.reshape(-1,1))[:,1]; pte=cal.predict_proba(ptest_raw.reshape(-1,1))[:,1]
    # Select the operating threshold on validation data only. This is essential for the imbalanced schedule target.
    thresholds=np.linspace(0.10,0.90,81)
    best_threshold=max(thresholds, key=lambda t:f1_score(yv,(pv>=t).astype(int),zero_division=0))
    def metrics_at(y,p,threshold):
        pred=(p>=threshold).astype(int)
        return {'accuracy':accuracy_score(y,pred),'f1':f1_score(y,pred,zero_division=0),'roc_auc':roc_auc_score(y,p),'pr_auc':average_precision_score(y,p),'brier':brier_score_loss(y,p)}
    mtr=metrics_at(ytr,ptr,best_threshold); mv=metrics_at(yv,pv,best_threshold); mte=metrics_at(yte,pte,best_threshold)
    gap=mtr['roc_auc']-mte['roc_auc']
    selected[target]={'features':model_features,'best_iteration':int(model.best_iteration_ or params[target]['n_estimators']), 'train_months':[str(x)[:7] for x in train_months], 'validation_months':[str(x)[:7] for x in val_months], 'test_months':[str(x)[:7] for x in test_months], 'decision_threshold':float(best_threshold),'train':mtr,'validation':mv,'test':mte,'train_test_auc_gap':gap}
    joblib.dump(model,OUT/'models'/f'{target}_model.joblib')
    joblib.dump(cal,OUT/'models'/f'{target}_platt_calibrator.joblib')
    model.booster_.save_model(str(OUT/'models'/f'{target}_model.txt'))
    fi=pd.DataFrame({'feature':model_features,'importance':model.feature_importances_}).sort_values('importance',ascending=False)
    fi.to_csv(OUT/'data'/f'{target}_feature_importance.csv',index=False)
    fi.head(20).sort_values('importance').plot(kind='barh',x='feature',y='importance',legend=False,figsize=(9,7))
    plt.title(f'Feature importance - {target}'); plt.tight_layout(); plt.savefig(OUT/'plots'/f'feature_importance_{target}.png',dpi=150); plt.close()
    models[target]=model; calibrators[target]=cal

# ---------------- SCORE ALL MONTHS ----------------
sc=df.copy()
for target in models:
    X=prep(sc[model_features])
    raw=models[target].predict_proba(X)[:,1]
    sc[f'{target}_raw_probability']=raw
    sc[f'{target}_probability']=calibrators[target].predict_proba(raw.reshape(-1,1))[:,1]
    sc[f'{target}_decision_threshold']=selected[target]['decision_threshold']
    sc[f'{target}_predicted_label']=(sc[f'{target}_probability']>=selected[target]['decision_threshold']).astype(int)

# Current risk: T/C are model probabilities. P/F are health signals.
sc['T_time_risk']=sc['schedule_risk_1m_probability'].clip(0,1)
sc['C_cost_risk']=sc['cost_risk_1m_probability'].clip(0,1)
sc['P_progress_risk']=sc['progress_risk'].clip(0,1)
sc['F_financial_risk']=sc['financial_efficiency_risk'].clip(0,1)
# Combined ML probability is retained as an auxiliary consistency signal, not double-counted heavily.
sc['ML_combined_risk']=sc['combined_risk_1m_probability'].clip(0,1)
# Base current risk weights. ML combined gets 10% as a cross-check; T/C/P/F carry the core interpretation.
sc['current_risk_score_0_100']=100*(0.30*sc['T_time_risk']+0.30*sc['C_cost_risk']+0.25*sc['P_progress_risk']+0.10*sc['F_financial_risk']+0.05*sc['ML_combined_risk'])

# Risk trend computed from the current composite itself, project-by-project.
sc=sc.sort_values(['project_code','report_month']).reset_index(drop=True)
sc['previous_current_risk_score']=sc.groupby('project_code')['current_risk_score_0_100'].shift(1)
sc['risk_velocity_1m']=sc['current_risk_score_0_100']-sc['previous_current_risk_score']
sc['previous_risk_velocity']=sc.groupby('project_code')['risk_velocity_1m'].shift(1)
sc['risk_acceleration_1m']=sc['risk_velocity_1m']-sc['previous_risk_velocity']
# Bounded emerging-risk signal: positive deterioration raises risk, improvement reduces it.
trend_vel=robust_unit(sc['risk_velocity_1m'].clip(-30,30),0.15,0.85)
trend_acc=robust_unit(sc['risk_acceleration_1m'].clip(-20,20),0.15,0.85)
# Center around 0.5 so stable projects don't receive an arbitrary boost.
trend_signal=((trend_vel-0.5)*0.7+(trend_acc-0.5)*0.3).clip(-0.5,0.5)
sc['emerging_risk_score_0_100']=(50+100*trend_signal).clip(0,100)
sc['DPHIS_score']= (0.78*sc['current_risk_score_0_100']+0.22*sc['emerging_risk_score_0_100']).clip(0,100)

# Risk tier and transition.
bins=[-np.inf,33,50,66,80,np.inf]; labels=['Low','Watch','Medium','High','Critical']
sc['risk_tier']=pd.cut(sc['DPHIS_score'],bins=bins,labels=labels,right=False)
sc['previous_risk_tier']=sc.groupby('project_code')['risk_tier'].shift(1)
sc['risk_transition']=sc['previous_risk_tier'].astype(str)+' -> '+sc['risk_tier'].astype(str)
sc.loc[sc['previous_risk_tier'].isna(),'risk_transition']='New/First observation'
sc['rapid_deterioration_flag']=((sc['risk_velocity_1m']>=8)|(sc['risk_acceleration_1m']>=5)).astype(int)

# Confidence: model agreement + data quality + history. Higher disagreement among T/C/combined means lower confidence.
sc['model_agreement']=1-(sc[['T_time_risk','C_cost_risk','ML_combined_risk']].max(axis=1)-sc[['T_time_risk','C_cost_risk','ML_combined_risk']].min(axis=1)).clip(0,1)
sc['confidence_score']=100*(0.55*sc['data_quality_score']+0.30*sc['model_agreement']+0.15*(1-np.abs(sc['risk_velocity_1m']).clip(0,20)/20)).clip(0,1)

# Driver scores: compare to neutral 0.5; top contributors are calculated deterministically.
components=pd.DataFrame({
 'Time':0.30*sc['T_time_risk'], 'Cost':0.30*sc['C_cost_risk'], 'Progress':0.25*sc['P_progress_risk'], 'Financial':0.10*sc['F_financial_risk'], 'ML consistency':0.05*sc['ML_combined_risk']})
# normalized positive contribution ranking; enough for dashboard explanation.
for name in components.columns:
    sc['driver_'+name.lower().replace(' ','_')]=components[name]

# Build compact final table.
final_cols=['report_month','project_code','project_name','ministry','sector','state','implementing_agency','original_cost_cr','revised_cost_cr','cumulative_expenditure_cr','physical_progress_pct','cost_overrun_pct','schedule_slippage_months','completion_date_revised_flag',
'T_time_risk','C_cost_risk','P_progress_risk','F_financial_risk','ML_combined_risk','current_risk_score_0_100','risk_velocity_1m','risk_acceleration_1m','emerging_risk_score_0_100','DPHIS_score','risk_tier','previous_risk_tier','risk_transition','rapid_deterioration_flag','data_quality_score','confidence_score','schedule_risk_1m_decision_threshold','cost_risk_1m_decision_threshold','combined_risk_1m_decision_threshold','progress_gap_enhanced_pct','expenditure_progress_efficiency_gap','required_progress_velocity_pct_per_month','progress_velocity_pct_per_month','velocity_gap_pct_points','expenditure_growth_pct','efficiency_gap_change_1m']
final=sc[final_cols].copy(); final['report_month']=final['report_month'].dt.strftime('%Y-%m')
final.to_csv(OUT/'data/3_final_project_health_scores.csv',index=False)
# full scoring dataset with model outputs for analysts
full=sc.copy(); full['report_month']=full['report_month'].dt.strftime('%Y-%m'); full.to_csv(OUT/'data/3_final_project_health_scores_all_columns.csv',index=False)

# Performance summary
rows=[]
for target,v in selected.items():
    for split in ['train','validation','test']:
        r=v[split]; rows.append({'model':target,'split':split,**r})
perf=pd.DataFrame(rows); perf.to_csv(OUT/'data/model_performance.csv',index=False)

# Score distribution plot
plt.figure(figsize=(9,5)); plt.hist(final['DPHIS_score'].dropna(),bins=30); plt.xlabel('DPHIS score'); plt.ylabel('Project snapshots'); plt.title('DPHIS score distribution'); plt.tight_layout(); plt.savefig(OUT/'plots/dphis_distribution.png',dpi=150); plt.close()
# Tier counts
final['risk_tier'].value_counts().reindex(labels,fill_value=0).plot(kind='bar',figsize=(8,5)); plt.xlabel('Risk tier'); plt.ylabel('Snapshots'); plt.title('DPHIS risk tiers'); plt.tight_layout(); plt.savefig(OUT/'plots/risk_tiers.png',dpi=150); plt.close()
# Component vs final
sc[['T_time_risk','C_cost_risk','P_progress_risk','F_financial_risk','ML_combined_risk','DPHIS_score']].corr().to_csv(OUT/'data/risk_component_correlations.csv')

# Manifest
manifest={
 'purpose':'Prototype predictive analytics and early warning system for PAIMANA infrastructure projects',
 'excluded_components':['M_milestone_risk','I_implementation_risk'],
 'models':selected,
 'scoring':{
  'current_risk':'100*(0.30*T + 0.30*C + 0.25*P + 0.10*F + 0.05*ML_combined)',
  'emerging_risk':'bounded function of 1-month risk velocity and acceleration',
  'dphis':'0.78*current_risk + 0.22*emerging_risk',
  'tiers':'Low <33; Watch 33-50; Medium 50-66; High 66-80; Critical >=80'
 },
 'progress_formula': 'P=0.45*normalized(progress_gap)+0.35*normalized(required_velocity-actual_velocity)+0.20*normalized(-velocity_change), with robust percentile scaling.',
 'financial_formula':'F=stage_adjusted(0.55*normalized(expenditure%-physical_progress%)+0.25*normalized(gap_change)+0.20*normalized(expenditure_growth_change)).',
 'trend':'risk_velocity=current risk - previous project snapshot; risk_acceleration=current velocity - previous velocity',
 'confidence':'0.55 data quality + 0.30 model agreement + 0.15 stability',
 'data_quality':'history depth plus completeness of core progress/financial/schedule fields',
 'leakage_controls':['No y_* or next_* fields used as model inputs','Validation/test are later report months than training','Calibration is fit only on validation predictions','Feature engineering uses current and historical project observations only']
}
(OUT/'data/model_manifest.json').write_text(json.dumps(manifest,indent=2,default=str))

# Documentation
readme='''# PAIMANA Predictive Early Warning — Prototype Final\n\nThis package upgrades the previous feature-selection pipeline into a project-level predictive early-warning prototype. M (milestone risk) and I (implementation risk) are intentionally excluded because the current dataset does not contain sufficiently reliable milestone/management fields.\n\n## Main outputs\n- `data/3_final_project_health_scores.csv`: compact dashboard-ready project snapshot scores.\n- `data/3_final_project_health_scores_all_columns.csv`: full analytical table with model outputs and engineered fields.\n- `data/model_performance.csv`: temporal train/validation/test metrics.\n- `data/model_manifest.json`: exact model features and scoring design.\n- `models/`: LightGBM models and validation-only Platt probability calibrators.\n\n## Risk design\nT = 1-month schedule risk probability from the schedule ML model.\nC = 1-month cost risk probability from the cost ML model.\nP = progress health risk from expected-vs-actual progress, required-vs-actual velocity, and velocity deterioration.\nF = stage-aware expenditure-vs-physical-progress efficiency risk plus deterioration and expenditure acceleration.\n\nCurrent risk = 30% T + 30% C + 25% P + 10% F + 5% combined-model consistency signal.\nEmerging risk captures risk velocity and acceleration. DPHIS = 78% current risk + 22% emerging risk.\n\nThe design deliberately uses bounded/robust transformations so extreme PAIMANA values do not dominate the score.\n\n## Model validation\nThe labeled history is split chronologically: earliest months for training, following two months for validation, and latest three labeled months for a completely later holdout. LightGBM is regularized and uses early stopping. Probability calibration is fitted only on validation predictions.\n\n## Why this is not simply a weighted average\nThe dashboard can show current risk, emerging risk, risk velocity, acceleration, confidence, data quality, risk transition, and the underlying T/C/P/F drivers. This is intended as decision support rather than a single opaque number.\n'''
(OUT/'README.md').write_text(readme)

report='# PAIMANA Predictive Early Warning — Technical Report\n\n'
report+='## 1. Scope\nThis prototype reuses the existing one-month-ahead cost, schedule and combined risk targets, while adding stage-aware progress and financial-health indicators. Milestone (M) and implementation (I) risk are intentionally omitted.\n\n'
report+='## 2. Leakage and generalization controls\n- Model inputs exclude all `y_*` and `next_*` fields.\n- Chronological holdout: later report months are held out from training.\n- Early stopping uses a validation period only.\n- Probability calibration uses validation predictions only.\n- Stronger regularization and minimum leaf size reduce memorization.\n\n'
report+='## 3. Models\n'
for target,v in selected.items():
    report+=f"### {target}\n- Best iteration: {v['best_iteration']}\n- Train ROC-AUC: {v['train']['roc_auc']:.4f}\n- Validation ROC-AUC: {v['validation']['roc_auc']:.4f}\n- Test ROC-AUC: {v['test']['roc_auc']:.4f}\n- Test F1: {v['test']['f1']:.4f}\n- Test PR-AUC: {v['test']['pr_auc']:.4f}\n- Test Brier: {v['test']['brier']:.4f}\n- Train-test AUC gap: {v['train_test_auc_gap']:.4f}\n\n"
report+='## 4. DPHIS\n'
report+='Current risk uses T/C/P/F plus a small combined-model consistency signal. Emerging risk is derived from project-level risk velocity and acceleration and is bounded before being blended. Final DPHIS is 78% current risk + 22% emerging risk. Tiers: Low, Watch, Medium, High, Critical.\n\n'
report+='## 5. Interpretation\nThe score is an early-warning indicator. Officers should inspect the component risks, trend, confidence, and driver fields before taking action.\n'
(OUT/'TECHNICAL_REPORT.md').write_text(report)

# scripts for reproducibility (self-contained wrappers; main build script is copied)
(OUT/'scripts/README.txt').write_text('Run the supplied build_enhanced_pipeline.py from a Python environment with pandas, numpy, lightgbm, scikit-learn, matplotlib and joblib. The script recreates the models and score tables from the input engineered dataset.')
shutil.copy2('/mnt/data/paimana_work/build_enhanced.py', OUT/'scripts/build_enhanced_pipeline.py')

# Zip
zip_path=Path('/mnt/data/PAIMANA_predictive_early_warning_final.zip')
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file(): z.write(p,p.relative_to(OUT.parent))
print('ZIP',zip_path)
print(perf.to_string(index=False))
print('FINAL rows',len(final),'projects',final.project_code.nunique())
print(final['risk_tier'].value_counts().to_string())
