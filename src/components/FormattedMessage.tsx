import React, { useState } from 'react';
import { 
  MapPin, 
  ArrowUpRight, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  ChevronRight, 
  Copy, 
  Check, 
  ShieldAlert,
  FileText
} from 'lucide-react';

interface Props {
  text: string;
  isDark?: boolean;
  onNavigateToProject?: (projectId: string) => void;
  isUser?: boolean;
}

interface ProjectSubItem {
  title: string;
  projectId?: string;
  metrics: string[];
  rawText: string;
}

interface ListGroup {
  title: string;
  stateName?: string;
  isStateGroup: boolean;
  projectItems: ProjectSubItem[];
  rawItems: string[];
}

export default function FormattedMessage({
  text,
  isDark = true,
  onNavigateToProject,
  isUser = false,
}: Props) {
  // If message is from user, display cleanly without markdown bloat
  if (isUser) {
    const cleanedUserText = text.replace(/[*#]/g, '').trim();
    return (
      <div className="leading-relaxed font-sans whitespace-pre-wrap">
        {cleanedUserText}
      </div>
    );
  }

  // Parse assistant response into structured blocks
  const blocks = parseContentBlocks(text);

  return (
    <div className="space-y-3 font-sans text-xs sm:text-sm leading-relaxed">
      {blocks.map((block, idx) => {
        switch (block.type) {
          case 'heading':
            return (
              <HeadingBlock
                key={idx}
                level={block.level || 3}
                text={block.text || ''}
                isDark={isDark}
                onNavigate={onNavigateToProject}
              />
            );

          case 'list-group':
            return (
              <ListGroupBlock
                key={idx}
                group={block.group!}
                isDark={isDark}
                onNavigate={onNavigateToProject}
              />
            );

          case 'numbered-list':
            return (
              <NumberedListBlock
                key={idx}
                items={block.lines || []}
                isDark={isDark}
                onNavigate={onNavigateToProject}
              />
            );

          case 'table':
            return (
              <TableBlock
                key={idx}
                rows={block.tableRows || []}
                isDark={isDark}
                onNavigate={onNavigateToProject}
              />
            );

          case 'code':
            return (
              <CodeBlock
                key={idx}
                code={block.code || ''}
                lang={block.lang || ''}
                isDark={isDark}
              />
            );

          case 'callout':
            return (
              <CalloutBlock
                key={idx}
                text={block.text || ''}
                isDark={isDark}
                onNavigate={onNavigateToProject}
              />
            );

          case 'paragraph':
          default:
            return (
              <p
                key={idx}
                className={`leading-relaxed ${
                  isDark ? 'text-white/90' : 'text-slate-800'
                }`}
              >
                {renderInline(block.text || '', isDark, onNavigateToProject)}
              </p>
            );
        }
      })}
    </div>
  );
}

// -------------------------------------------------------------
// Block Parsing
// -------------------------------------------------------------
interface ContentBlock {
  type: 'heading' | 'list-group' | 'numbered-list' | 'table' | 'code' | 'callout' | 'paragraph';
  level?: number;
  text?: string;
  code?: string;
  lang?: string;
  lines?: string[];
  tableRows?: string[][];
  group?: ListGroup;
}

function parseContentBlocks(markdown: string): ContentBlock[] {
  const lines = markdown.split(/\r?\n/);
  const blocks: ContentBlock[] = [];
  let i = 0;

  while (i < lines.length) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      i++;
      continue;
    }

    // 1. Code blocks (```lang ... ```)
    if (trimmed.startsWith('```')) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      blocks.push({
        type: 'code',
        code: codeLines.join('\n'),
        lang,
      });
      continue;
    }

    // 2. Headings (#, ##, ###, ####)
    const headerMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (headerMatch) {
      blocks.push({
        type: 'heading',
        level: headerMatch[1].length,
        text: headerMatch[2],
      });
      i++;
      continue;
    }

    // 3. Tables (| col | col |)
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.length > 2) {
      const tableLines: string[] = [];
      while (
        i < lines.length &&
        lines[i].trim().startsWith('|') &&
        lines[i].trim().endsWith('|')
      ) {
        // Skip separator row |---|---|
        if (!/^[\|\s\-:]+$/.test(lines[i].trim())) {
          tableLines.push(lines[i].trim());
        }
        i++;
      }
      const tableRows = tableLines.map(l =>
        l
          .slice(1, -1)
          .split('|')
          .map(cell => cell.trim())
      );
      blocks.push({ type: 'table', tableRows });
      continue;
    }

    // 4. Bullet lists (*, -, •)
    if (/^\s*[*•\-]\s+/.test(rawLine)) {
      const listLines: string[] = [];
      while (
        i < lines.length &&
        (/^\s*[*•\-]\s+/.test(lines[i]) ||
          (/^\s{2,}/.test(lines[i]) && lines[i].trim().length > 0))
      ) {
        listLines.push(lines[i]);
        i++;
      }

      const groups = parseListGroupLines(listLines);
      for (const g of groups) {
        blocks.push({
          type: 'list-group',
          group: g,
        });
      }
      continue;
    }

    // 5. Numbered lists (1. , 2. )
    if (/^\s*\d+\.\s+/.test(trimmed)) {
      const numLines: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i].trim())) {
        numLines.push(lines[i].trim().replace(/^\d+\.\s+/, ''));
        i++;
      }
      blocks.push({
        type: 'numbered-list',
        lines: numLines,
      });
      continue;
    }

    // 6. Callouts & Telemetry tags
    if (
      /^(evidence\s*&?\s*verified\s*telemetry|telemetry|high-risk\s*classification|critical\s*alert|note|attention):/i.test(
        trimmed
      )
    ) {
      blocks.push({
        type: 'callout',
        text: trimmed,
      });
      i++;
      continue;
    }

    // 7. Regular paragraphs
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith('#') &&
      !lines[i].trim().startsWith('```') &&
      !/^\s*[*•\-]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i].trim()) &&
      !(lines[i].trim().startsWith('|') && lines[i].trim().endsWith('|')) &&
      !/^(evidence\s*&?\s*verified\s*telemetry|telemetry|high-risk\s*classification|critical\s*alert|note|attention):/i.test(
        lines[i].trim()
      )
    ) {
      paraLines.push(lines[i].trim());
      i++;
    }

    if (paraLines.length > 0) {
      blocks.push({
        type: 'paragraph',
        text: paraLines.join(' '),
      });
    }
  }

  return blocks;
}

// Parse lines belonging to bullet lists into groups
function parseListGroupLines(lines: string[]): ListGroup[] {
  const groups: ListGroup[] = [];
  let current: ListGroup | null = null;

  for (const line of lines) {
    const indent = line.search(/\S/);
    const content = line.replace(/^\s*[*•\-]\s+/, '').trim();

    // Check if line represents an indented sub-item under the current group
    if (indent >= 2 && current) {
      const parsedSub = parseProjectSubItem(content);
      if (parsedSub.projectId || parsedSub.metrics.length > 0) {
        current.projectItems.push(parsedSub);
      } else {
        current.rawItems.push(content);
      }
    } else {
      // Top-level item
      // Check if it's a state/group header like **Gujarat:** or Gujarat:
      const cleanTitle = content.replace(/[*#]/g, '').trim();
      const stateMatch = cleanTitle.match(/^([A-Za-z\s]+):$/);
      const isStateGroup = Boolean(
        stateMatch ||
          /^(Gujarat|Maharashtra|Delhi|Uttarakhand|Uttar Pradesh|Karnataka|Tamil Nadu|Telangana|West Bengal|Bihar|Madhya Pradesh|Rajasthan|Punjab|Haryana|Odisha|Kerala|Assam|Andhra Pradesh|Jharkhand|Chhattisgarh|Goa):?/i.test(
            cleanTitle
          )
      );

      current = {
        title: content,
        stateName: cleanTitle.replace(/:$/, ''),
        isStateGroup,
        projectItems: [],
        rawItems: [],
      };
      groups.push(current);
    }
  }

  return groups;
}

// Parses a line like: *Ahmedabad Metro Rail Project [Phase-I]* (ID: 702639) | Progress: 99.99% | Delay: 98 months
function parseProjectSubItem(raw: string): ProjectSubItem {
  // Strip bullet if present
  let clean = raw.replace(/^\s*[*•\-]\s+/, '').trim();

  // Find Project ID: (ID: N28000122) or ID: 702639
  const idMatch =
    clean.match(/\(ID:\s*([A-Za-z0-9_\-]+)\)/i) ||
    clean.match(/\bID:\s*([A-Za-z0-9_\-]+)\b/i);
  const projectId = idMatch ? idMatch[1] : undefined;

  // Split by pipe |
  const parts = clean.split('|').map(s => s.trim());
  let titlePart = parts[0];

  if (projectId) {
    // Remove (ID: ...) from the title
    titlePart = titlePart
      .replace(/\(ID:\s*[A-Za-z0-9_\-]+\)/i, '')
      .replace(/\bID:\s*[A-Za-z0-9_\-]+\b/i, '')
      .trim();
  }

  // Clean asterisks and underscores from title
  titlePart = titlePart.replace(/^[*_\s]+/, '').replace(/[*_\s]+$/, '').trim();

  // Metrics are any subsequent pipe segments
  const metrics = parts.slice(1).map(m => m.replace(/[*#]/g, '').trim());

  return {
    title: titlePart || 'Infrastructure Corridor',
    projectId,
    metrics,
    rawText: raw,
  };
}

// -------------------------------------------------------------
// Sub-components for rendering blocks
// -------------------------------------------------------------

function HeadingBlock({
  level,
  text,
  isDark,
  onNavigate,
}: {
  level: number;
  text: string;
  isDark: boolean;
  onNavigate?: (pid: string) => void;
}) {
  const cleanTitle = text.replace(/[*#]/g, '').trim();

  if (level === 1) {
    return (
      <div className={`mt-3 mb-2 pb-1.5 border-b flex items-center gap-2 ${
        isDark ? 'border-white/15 text-white font-bold text-base sm:text-lg' : 'border-slate-300 text-slate-900 font-bold text-base sm:text-lg'
      }`}>
        <span className="w-2 h-4 rounded-full bg-cyan-400 inline-block shrink-0" />
        <span>{renderInline(cleanTitle, isDark, onNavigate)}</span>
      </div>
    );
  }

  if (level === 2) {
    return (
      <div className={`mt-3 mb-1.5 flex items-center gap-2 font-bold text-sm sm:text-base ${
        isDark ? 'text-cyan-300' : 'text-blue-800'
      }`}>
        <span className="w-1.5 h-3.5 rounded-full bg-cyan-400 inline-block shrink-0" />
        <span>{renderInline(cleanTitle, isDark, onNavigate)}</span>
      </div>
    );
  }

  // Level 3 & 4
  return (
    <div className={`mt-2.5 mb-1.5 flex items-center gap-2 font-semibold text-xs sm:text-sm tracking-wide ${
      isDark ? 'text-white' : 'text-slate-900'
    }`}>
      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 shadow-xs" />
      <span className="uppercase text-[11px] sm:text-xs font-mono font-bold tracking-wider opacity-90">
        {renderInline(cleanTitle, isDark, onNavigate)}
      </span>
    </div>
  );
}

function ListGroupBlock({
  group,
  isDark,
  onNavigate,
}: {
  group: ListGroup;
  isDark: boolean;
  onNavigate?: (pid: string) => void;
}) {
  const hasSubItems = group.projectItems.length > 0 || group.rawItems.length > 0;

  // Case 1: State / Category group with structured sub-items
  if (group.isStateGroup && hasSubItems) {
    return (
      <div className="space-y-2 my-2.5">
        {/* State / Group Header */}
        <div className="flex items-center gap-2 pt-1 font-semibold text-xs sm:text-sm">
          <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className={`font-bold tracking-wide uppercase ${isDark ? 'text-cyan-300' : 'text-blue-700'}`}>
            {group.stateName || group.title.replace(/[*#:]/g, '').trim()}
          </span>
          {group.projectItems.length > 0 && (
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                isDark
                  ? 'bg-white/10 text-white/70 border-white/15'
                  : 'bg-slate-100 text-slate-700 border-slate-300'
              }`}
            >
              {group.projectItems.length}{' '}
              {group.projectItems.length === 1 ? 'project' : 'projects'}
            </span>
          )}
        </div>

        {/* Structured Project Sub-Cards */}
        <div className="space-y-1.5 pl-3 sm:pl-4 border-l-2 border-cyan-500/30">
          {group.projectItems.map((item, pIdx) => (
            <ProjectCardItem
              key={pIdx}
              item={item}
              isDark={isDark}
              onNavigate={onNavigate}
            />
          ))}

          {/* Fallback raw sub-items */}
          {group.rawItems.map((raw, rIdx) => (
            <div key={rIdx} className="flex items-start gap-2 text-xs sm:text-sm py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-white/40 mt-1.5 shrink-0" />
              <span className={isDark ? 'text-white/80' : 'text-slate-700'}>
                {renderInline(raw, isDark, onNavigate)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Case 2: Group that isn't a state header, but has sub-items
  if (hasSubItems) {
    return (
      <div className="space-y-1.5 my-2">
        <div className="flex items-center gap-2 font-semibold text-xs sm:text-sm">
          <ChevronRight className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span className={isDark ? 'text-white' : 'text-slate-900'}>
            {renderInline(group.title, isDark, onNavigate)}
          </span>
        </div>
        <div className="space-y-1 pl-4 border-l border-white/10">
          {group.projectItems.map((item, pIdx) => (
            <ProjectCardItem
              key={pIdx}
              item={item}
              isDark={isDark}
              onNavigate={onNavigate}
            />
          ))}
          {group.rawItems.map((raw, rIdx) => (
            <div key={rIdx} className="flex items-start gap-2 text-xs py-0.5">
              <span className="w-1 h-1 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
              <span>{renderInline(raw, isDark, onNavigate)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Case 3: Flat bullet item (single line)
  return (
    <div className="flex items-start gap-2.5 my-1 text-xs sm:text-sm leading-relaxed">
      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 shrink-0 shadow-xs" />
      <div className={`flex-1 ${isDark ? 'text-white/90' : 'text-slate-800'}`}>
        {renderInline(group.title, isDark, onNavigate)}
      </div>
    </div>
  );
}

function ProjectCardItem({
  item,
  isDark,
  onNavigate,
}: {
  item: ProjectSubItem;
  isDark: boolean;
  onNavigate?: (pid: string) => void;
}) {
  return (
    <div
      className={`p-2.5 sm:p-3 rounded-xl border transition-all ${
        isDark
          ? 'bg-white/[0.04] border-white/10 hover:border-white/25 hover:bg-white/[0.07]'
          : 'bg-white border-slate-200 shadow-xs hover:border-slate-300'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        {/* Project Name and Interactive ID */}
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          <span
            className={`font-semibold text-xs sm:text-sm truncate ${
              isDark ? 'text-white' : 'text-slate-900'
            }`}
          >
            {item.title}
          </span>

          {item.projectId && (
            <button
              type="button"
              onClick={() => onNavigate?.(item.projectId!)}
              title={`View telemetry for project ${item.projectId}`}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium transition-colors cursor-pointer ${
                isDark
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/25 hover:border-cyan-400'
                  : 'bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100'
              }`}
            >
              <span>ID: {item.projectId}</span>
              <ArrowUpRight className="w-3 h-3 opacity-70" />
            </button>
          )}
        </div>

        {/* Metrics Badges (Progress, Delay, Cost, etc.) */}
        {item.metrics.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap shrink-0">
            {item.metrics.map((m, mIdx) => {
              const isDelay = /delay/i.test(m);
              const isSignificantDelay =
                isDelay &&
                !/N\/A/i.test(m) &&
                !/0(\.0+)?\s*(mo|month)/i.test(m);
              const isProgress = /progress/i.test(m);
              const isCost = /cost|budget|outlay|₹/i.test(m);

              return (
                <span
                  key={mIdx}
                  className={`px-2 py-0.5 rounded-md text-[11px] font-mono font-medium border inline-flex items-center gap-1 ${
                    isSignificantDelay
                      ? isDark
                        ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                        : 'bg-amber-50 text-amber-800 border-amber-200'
                      : isProgress
                      ? isDark
                        ? 'bg-blue-500/15 text-blue-300 border-blue-500/30'
                        : 'bg-blue-50 text-blue-700 border-blue-200'
                      : isCost
                      ? isDark
                        ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                        : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : isDark
                      ? 'bg-white/10 text-white/80 border-white/15'
                      : 'bg-slate-100 text-slate-700 border-slate-200'
                  }`}
                >
                  {isSignificantDelay && (
                    <Clock className="w-3 h-3 text-amber-400 shrink-0" />
                  )}
                  {isProgress && (
                    <CheckCircle2 className="w-3 h-3 text-blue-400 shrink-0" />
                  )}
                  <span>{m}</span>
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function NumberedListBlock({
  items,
  isDark,
  onNavigate,
}: {
  items: string[];
  isDark: boolean;
  onNavigate?: (pid: string) => void;
}) {
  return (
    <div className="space-y-1.5 my-2">
      {items.map((item, idx) => (
        <div
          key={idx}
          className="flex items-start gap-2.5 text-xs sm:text-sm leading-relaxed"
        >
          <span
            className={`shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono font-bold mt-0.5 ${
              isDark
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'bg-blue-100 text-blue-800 border border-blue-200'
            }`}
          >
            {idx + 1}
          </span>
          <div
            className={`flex-1 ${isDark ? 'text-white/90' : 'text-slate-800'}`}
          >
            {renderInline(item, isDark, onNavigate)}
          </div>
        </div>
      ))}
    </div>
  );
}

function CalloutBlock({
  text,
  isDark,
  onNavigate,
}: {
  text: string;
  isDark: boolean;
  onNavigate?: (pid: string) => void;
}) {
  const isHighRisk = /high-risk|critical|alert|immediate/i.test(text);

  return (
    <div
      className={`my-2.5 p-3 rounded-xl border flex items-start gap-2.5 ${
        isHighRisk
          ? isDark
            ? 'bg-rose-500/10 border-rose-500/30 text-rose-200'
            : 'bg-rose-50 border-rose-200 text-rose-900'
          : isDark
          ? 'bg-cyan-500/10 border-cyan-500/25 text-cyan-200'
          : 'bg-blue-50 border-blue-200 text-blue-900'
      }`}
    >
      {isHighRisk ? (
        <ShieldAlert className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
      ) : (
        <FileText className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
      )}
      <div className="text-xs sm:text-sm leading-relaxed">
        {renderInline(text, isDark, onNavigate)}
      </div>
    </div>
  );
}

function TableBlock({
  rows,
  isDark,
  onNavigate,
}: {
  rows: string[][];
  isDark: boolean;
  onNavigate?: (pid: string) => void;
}) {
  if (rows.length === 0) return null;
  const header = rows[0];
  const bodyRows = rows.slice(1);

  return (
    <div className="overflow-x-auto my-3 rounded-xl border border-white/10">
      <table className="w-full text-left text-xs border-collapse">
        <thead>
          <tr className={isDark ? 'bg-white/10 text-white font-mono' : 'bg-slate-100 text-slate-800 font-mono'}>
            {header.map((col, idx) => (
              <th key={idx} className="p-2.5 border-b border-white/10 font-bold">
                {col.replace(/[*#]/g, '').trim()}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bodyRows.map((row, rIdx) => (
            <tr
              key={rIdx}
              className={`border-b ${
                isDark
                  ? 'border-white/5 hover:bg-white/[0.04]'
                  : 'border-slate-200 hover:bg-slate-50'
              }`}
            >
              {row.map((cell, cIdx) => (
                <td key={cIdx} className="p-2.5">
                  {renderInline(cell, isDark, onNavigate)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CodeBlock({
  code,
  lang,
  isDark,
}: {
  code: string;
  lang: string;
  isDark: boolean;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`my-3 rounded-xl border overflow-hidden ${
        isDark ? 'bg-black/60 border-white/15' : 'bg-slate-900 text-slate-100 border-slate-700'
      }`}
    >
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/10 bg-white/5 text-[11px] font-mono">
        <span className="opacity-70">{lang || 'text'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity cursor-pointer"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre className="p-3 text-xs font-mono overflow-x-auto whitespace-pre leading-normal">
        <code>{code}</code>
      </pre>
    </div>
  );
}

// -------------------------------------------------------------
// Inline Formatter
// -------------------------------------------------------------

function renderInline(
  text: string,
  isDark: boolean,
  onNavigate?: (pid: string) => void
): React.ReactNode {
  if (!text) return null;

  // Tokenize string for code, bold, italic, and project IDs
  const pattern =
    /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\(ID:\s*[A-Za-z0-9_\-]+\)|ID:\s*[A-Za-z0-9_\-]+)/g;

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const plain = text
        .substring(lastIndex, match.index)
        .replace(/[*#]/g, ''); // strip any loose asterisks or hashes
      if (plain) parts.push(plain);
    }

    const raw = match[0];
    const key = `token-${match.index}`;

    if (raw.startsWith('`') && raw.endsWith('`')) {
      parts.push(
        <code
          key={key}
          className={`font-mono text-[11px] px-1.5 py-0.5 rounded border ${
            isDark
              ? 'bg-white/10 text-cyan-300 border-white/15'
              : 'bg-slate-100 text-slate-800 border-slate-300'
          }`}
        >
          {raw.slice(1, -1)}
        </code>
      );
    } else if (raw.startsWith('**') && raw.endsWith('**')) {
      const boldText = raw.slice(2, -2).trim();
      parts.push(
        <strong
          key={key}
          className={`font-semibold ${isDark ? 'text-white' : 'text-slate-950'}`}
        >
          {boldText}
        </strong>
      );
    } else if (raw.startsWith('*') && raw.endsWith('*')) {
      const italicText = raw.slice(1, -1).trim();
      parts.push(
        <em
          key={key}
          className={`italic font-medium ${isDark ? 'text-white/95' : 'text-slate-900'}`}
        >
          {italicText}
        </em>
      );
    } else if (/ID:/i.test(raw)) {
      const idMatch = raw.match(/ID:\s*([A-Za-z0-9_\-]+)/i);
      const pid = idMatch ? idMatch[1] : '';
      if (pid) {
        parts.push(
          <button
            key={key}
            type="button"
            onClick={() => onNavigate?.(pid)}
            title={`View project ${pid}`}
            className={`inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded font-mono text-[11px] border transition-colors cursor-pointer mx-1 ${
              isDark
                ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30 hover:bg-cyan-500/20 hover:border-cyan-400'
                : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
            }`}
          >
            <span>ID: {pid}</span>
            <ArrowUpRight className="w-2.5 h-2.5 opacity-70" />
          </button>
        );
      } else {
        parts.push(raw.replace(/[*#]/g, ''));
      }
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    const trailing = text.substring(lastIndex).replace(/[*#]/g, '');
    if (trailing) parts.push(trailing);
  }

  return parts;
}
