import { useInView } from '../motion';

/**
 * Technology section.
 *
 * Each technology is shown with the role it plays, grouped by layer. A logo
 * wall would communicate nothing; the role is the point.
 */

const LAYERS = [
  {
    id: 'interface',
    name: 'Interface',
    purpose: 'What the user operates',
    items: [
      { name: 'React', role: 'Component and interaction layer' },
      { name: 'TypeScript', role: 'Static correctness across the contract boundary' },
    ],
  },
  {
    id: 'services',
    name: 'Services',
    purpose: 'What serves the data',
    items: [
      { name: 'FastAPI', role: 'Typed backend services and aggregation' },
      { name: 'MongoDB', role: 'Flexible document storage for project records' },
    ],
  },
  {
    id: 'intelligence',
    name: 'Intelligence',
    purpose: 'What predicts and explains',
    items: [
      { name: 'XGBoost', role: 'Predictive layer for cost and schedule risk' },
      { name: 'SHAP', role: 'Driver attribution behind every risk score' },
      { name: 'Agent', role: 'Stateful investigation across evidence sources' },
      { name: 'MCP', role: 'Standardised tool access for the investigator' },
    ],
  },
  {
    id: 'operations',
    name: 'Operations',
    purpose: 'What runs and watches it',
    items: [
      { name: 'Python', role: 'Agent runtime and model integration' },
      { name: 'n8n', role: 'Workflow automation after decisions are made' },
      { name: 'Langfuse', role: 'Tracing and observability for agent runs' },
    ],
  },
];

const PRINCIPLES = [
  {
    title: 'Domain logic stays on the server',
    body: 'DPHIS calculation, threshold logic, agent decisions, and authorisation are resolved in the backend. The browser visualises those states rather than recomputing them.',
  },
  {
    title: 'Automation follows decisions',
    body: 'n8n executes workflows that have already been decided and authorised. Business logic is not moved into the automation layer.',
  },
  {
    title: 'Every prediction is explainable',
    body: 'A score that cannot be attributed to drivers is not usable in a decision review. SHAP attribution ships with the score.',
  },
];

export default function TechnologySection() {
  const { ref, isInView } = useInView<HTMLElement>();

  return (
    <section className="lp-section lp-tech" id="technology" ref={ref}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">Technology</span>
          <h2 className="lp-section__title">A foundation chosen for inspectability.</h2>
          <p className="lp-section__description">
            The stack is deliberately conventional. Each layer has one job, boundaries between layers
            are explicit, and the parts that make a claim auditable — attribution, tracing, and
            authorisation — are first-class rather than bolted on.
          </p>
        </div>

        <div className="lp-tech__layers" data-visible={isInView ? 'true' : 'false'}>
          {LAYERS.map((layer) => (
            <section key={layer.id} className="lp-tech__layer">
              <header className="lp-tech__layer-header">
                <h3 className="lp-tech__layer-name">{layer.name}</h3>
                <span className="lp-tech__layer-purpose">{layer.purpose}</span>
              </header>
              <ul className="lp-tech__items">
                {layer.items.map((item) => (
                  <li key={item.name} className="lp-tech__item">
                    <span className="lp-tech__item-name">{item.name}</span>
                    <span className="lp-tech__item-role">{item.role}</span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        <div className="lp-tech__principles">
          {PRINCIPLES.map((principle, index) => (
            <div key={principle.title} className="lp-tech__principle">
              <span className="lp-tech__principle-index" aria-hidden="true">
                {String(index + 1).padStart(2, '0')}
              </span>
              <div>
                <h4 className="lp-tech__principle-title">{principle.title}</h4>
                <p className="lp-tech__principle-body">{principle.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}