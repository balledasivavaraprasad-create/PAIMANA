import { describe, it, expect } from 'vitest';
import { sendChatMessage } from '../lib/api';

describe('PAIMANA Interactive Intelligence Assistant Tests', () => {
  it('replies with "Hello! My name is PAIMANA Intelligence" when user greets', async () => {
    const resHi = await sendChatMessage('hi');
    expect(resHi.reply).toContain('Hello! My name is PAIMANA Intelligence');
    // Must NOT inject project dossier or project details
    expect(resHi.reply).not.toContain('Project Intelligence Dossier');
    expect(resHi.reply).not.toContain('Systemic delay risks');

    const resHello = await sendChatMessage('hello');
    expect(resHello.reply).toContain('Hello! My name is PAIMANA Intelligence');

    const resHey = await sendChatMessage('hey there');
    expect(resHey.reply).toContain('Hello! My name is PAIMANA Intelligence');
  });

  it('answers "who are you" / capabilities without injecting unsolicited project dossiers', async () => {
    const res = await sendChatMessage('who are you?');
    expect(res.reply).toContain('PAIMANA Intelligence');
    expect(res.reply).toContain('What I Can Help You With');
    expect(res.reply).not.toContain('Project Intelligence Dossier');
    expect(res.intent).toBe('IDENTITY');
  });

  it('explains DPHIS calculation accurately without unsolicited project dossiers', async () => {
    const res = await sendChatMessage('What is DPHIS and how is it calculated?');
    expect(res.reply).toContain('Dynamic Project Health & Integrity Score');
    expect(res.reply).toContain('Schedule Slippage Velocity');
    expect(res.reply).toContain('Physical-Financial Burn Disparity');
    expect(res.reply).toContain('Risk Tier Thresholds');
    expect(res.reply).not.toContain('Project Intelligence Dossier');
    expect(res.intent).toBe('DPHIS_EXPLANATION');
  });

  it('explains Machine Learning and SHAP explainability accurately', async () => {
    const res = await sendChatMessage('What machine learning models do you use?');
    expect(res.reply).toContain('XGBoost');
    expect(res.reply).toContain('TreeSHAP');
    expect(res.reply).not.toContain('Project Intelligence Dossier');
    expect(res.intent).toBe('ML_EXPLANATION');
  });

  it('answers general questions directly and does not mention projects when not asked', async () => {
    const res = await sendChatMessage('What is the capital of India?');
    expect(res.reply).toContain('New Delhi');
    expect(res.reply).not.toContain('Project Intelligence Dossier');

    const resJoke = await sendChatMessage('tell me a joke');
    expect(resJoke.reply).toContain('😄');
    expect(resJoke.reply).not.toContain('Project Intelligence Dossier');
  });

  it('provides project details ONLY when the user explicitly asks about a project', async () => {
    // 1. Querying a specific project by name
    const resAhmedabad = await sendChatMessage('Tell me about Ahmedabad Metro');
    expect(resAhmedabad.reply).toContain('Ahmedabad Metro');
    expect(resAhmedabad.intent).toBe('PROJECT_INTELLIGENCE');

    // 2. Querying a specific project by ID
    const resId = await sendChatMessage('What is the status of N28000157?');
    expect(resId.reply).toContain('N28000157');
    expect(resId.intent).toBe('PROJECT_INTELLIGENCE');

    // 3. User explicitly asking to show projects
    const resProjects = await sendChatMessage('Show my projects');
    expect(resProjects.reply).toContain('Monitored Infrastructure Portfolio Overview');
    expect(resProjects.intent).toBe('PORTFOLIO_SUMMARY');

    // 4. User asking about recent changes / delays
    const resChanges = await sendChatMessage('What are the recent delay changes?');
    expect(resChanges.reply).toContain('projects with active schedule delay changes');
    expect(resChanges.intent).toBe('CHANGES');
  });
});
