import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSlug from 'rehype-slug';
import mermaid from 'mermaid';
import { Download, List, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, sans-serif',
  darkMode: true,
  themeVariables: {
    primaryColor: '#1e3a5f',
    primaryTextColor: '#e2e8f0',
    primaryBorderColor: '#3b82f6',
    lineColor: '#64748b',
    secondaryColor: '#0f172a',
    tertiaryColor: '#1e293b',
  },
});

interface MarkdownRendererProps {
  content: string;
}

interface TocItem {
  id: string;
  text: string;
  level: number;
}

function extractToc(markdown: string): TocItem[] {
  const lines = markdown.split('\n');
  const items: TocItem[] = [];
  for (const line of lines) {
    const match = line.match(/^(#{1,3})\s+(.+)/);
    if (match) {
      const level = match[1].length;
      const text = match[2].replace(/[*_`]/g, '').trim();
      const id = text.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-');
      items.push({ id, text, level });
    }
  }
  return items;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tocOpen, setTocOpen] = useState(true);
  const [activeId, setActiveId] = useState('');
  const toc = extractToc(content);

  useEffect(() => {
    if (!containerRef.current) return;
    // Re-run mermaid on all .mermaid divs after render
    mermaid.run({ nodes: containerRef.current.querySelectorAll('.mermaid') as any })
      .catch(e => console.error('Mermaid render error', e));
  }, [content]);

  // Highlight active ToC item on scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) setActiveId(entry.target.id);
        }
      },
      { rootMargin: '-20% 0px -70% 0px' }
    );
    const headings = containerRef.current?.querySelectorAll('h1,h2,h3') ?? [];
    headings.forEach(h => observer.observe(h));
    return () => observer.disconnect();
  }, [content]);

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'system_design.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  const scrollToHeading = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="w-full relative flex gap-0">

      {/* ── Table of Contents sidebar ──────────────────────────────── */}
      {toc.length > 0 && (
        <aside className={`hidden xl:block shrink-0 transition-all duration-300 ${tocOpen ? 'w-64' : 'w-0 overflow-hidden'}`}>
          <div className="sticky top-20 w-64 max-h-[calc(100vh-6rem)] overflow-y-auto pr-2">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Contents</span>
              <button onClick={() => setTocOpen(false)} className="text-slate-600 hover:text-slate-400">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <nav className="space-y-0.5">
              {toc.map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollToHeading(item.id)}
                  className={`block w-full text-left text-xs py-1 px-2 rounded transition-colors truncate ${
                    item.level === 1 ? 'font-semibold' :
                    item.level === 2 ? 'pl-4 font-medium' : 'pl-7 font-normal'
                  } ${
                    activeId === item.id
                      ? 'text-blue-400 bg-blue-500/10'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
                  }`}
                >
                  {item.text}
                </button>
              ))}
            </nav>
          </div>
        </aside>
      )}

      {/* ── Main content ──────────────────────────────────────────── */}
      <div className="flex-1 min-w-0">
        {/* Toolbar */}
        <div className="flex items-center justify-between mb-6 gap-4">
          <div className="flex items-center gap-3">
            {!tocOpen && (
              <Button variant="ghost" size="sm" onClick={() => setTocOpen(true)} className="text-slate-400 hover:text-slate-200 gap-2">
                <List className="w-4 h-4" /> Contents
              </Button>
            )}
            <div className="h-1 w-24 bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full" />
            <span className="text-sm text-slate-400 font-medium">System Design Document</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
            className="border-slate-700 hover:bg-slate-800 text-slate-300 gap-2"
          >
            <Download className="w-4 h-4" />
            Download .md
          </Button>
        </div>

        {/* Document body */}
        <div
          ref={containerRef}
          className="
            prose prose-invert prose-slate max-w-none
            prose-headings:scroll-mt-24
            prose-h1:text-3xl prose-h1:font-extrabold prose-h1:text-white prose-h1:border-b prose-h1:border-slate-700 prose-h1:pb-4 prose-h1:mb-6
            prose-h2:text-xl prose-h2:font-bold prose-h2:text-slate-100 prose-h2:mt-10 prose-h2:mb-4 prose-h2:border-l-4 prose-h2:border-blue-500 prose-h2:pl-4
            prose-h3:text-base prose-h3:font-semibold prose-h3:text-blue-300 prose-h3:mt-6
            prose-p:text-slate-300 prose-p:leading-7
            prose-li:text-slate-300
            prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
            prose-strong:text-slate-100 prose-strong:font-semibold
            prose-code:text-blue-300 prose-code:bg-slate-800/70 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
            prose-pre:bg-slate-950 prose-pre:border prose-pre:border-slate-800 prose-pre:rounded-xl prose-pre:my-6
            prose-blockquote:border-l-blue-500 prose-blockquote:text-slate-400 prose-blockquote:bg-slate-800/30 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:rounded-r-lg
            prose-table:border-collapse
            prose-hr:border-slate-700 prose-hr:my-8
          "
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeSlug]}
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                const lang = match?.[1];
                const isMermaid = lang === 'mermaid';

                if (!inline && isMermaid) {
                  return (
                    <div className="mermaid-wrapper my-8 p-2 bg-slate-950/80 rounded-2xl border border-slate-700/50 shadow-xl overflow-x-auto">
                      <div
                        className="mermaid flex justify-center items-center min-h-[200px]"
                      >
                        {String(children).replace(/\n$/, '')}
                      </div>
                    </div>
                  );
                }

                if (!inline) {
                  return (
                    <div className="relative group">
                      {lang && (
                        <span className="absolute top-3 right-3 text-xs text-slate-500 font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                          {lang}
                        </span>
                      )}
                      <code className={className} {...props}>{children}</code>
                    </div>
                  );
                }

                return (
                  <code className="bg-slate-800/70 text-blue-300 px-1.5 py-0.5 rounded text-sm" {...props}>
                    {children}
                  </code>
                );
              },

              table({ children, ...props }) {
                return (
                  <div className="overflow-x-auto my-6 rounded-xl border border-slate-700/50 shadow-lg">
                    <table className="w-full border-collapse text-sm" {...props}>
                      {children}
                    </table>
                  </div>
                );
              },
              thead({ children, ...props }) {
                return <thead className="bg-slate-800/80" {...props}>{children}</thead>;
              },
              th({ children, ...props }) {
                return (
                  <th className="border-b border-slate-700 px-4 py-3 text-left font-semibold text-slate-200 whitespace-nowrap" {...props}>
                    {children}
                  </th>
                );
              },
              td({ children, ...props }) {
                return (
                  <td className="border-b border-slate-800/60 px-4 py-2.5 text-slate-300 align-top" {...props}>
                    {children}
                  </td>
                );
              },
              tr({ children, ...props }) {
                return (
                  <tr className="hover:bg-slate-800/30 transition-colors" {...props}>
                    {children}
                  </tr>
                );
              },

              h1({ children, id, ...props }) {
                return <h1 id={id} {...props}>{children}</h1>;
              },
              h2({ children, id, ...props }) {
                return <h2 id={id} {...props}>{children}</h2>;
              },
              h3({ children, id, ...props }) {
                return <h3 id={id} {...props}>{children}</h3>;
              },

              ul({ children, ...props }) {
                return <ul className="space-y-1.5 my-4" {...props}>{children}</ul>;
              },
              li({ children, ...props }) {
                return (
                  <li className="flex gap-2 items-start text-slate-300" {...props}>
                    {children}
                  </li>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* Bottom action bar */}
        <div className="mt-12 pt-8 border-t border-slate-800 flex items-center justify-between">
          <p className="text-sm text-slate-500">Generated by ArchitectFlow AI Pipeline</p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
            className="border-slate-700 hover:bg-slate-800 text-slate-300 gap-2"
          >
            <Download className="w-4 h-4" />
            Download Markdown
          </Button>
        </div>
      </div>
    </div>
  );
};
