import React from 'react';

interface CardProps {
    title?: string;
    description?: string;
    children: React.ReactNode;
    className?: string;
    action?: React.ReactNode;
    footer?: React.ReactNode;
    /** Small uppercase label above the title, in the accent colour. */
    eyebrow?: string;
    /** Accent icon rendered beside the title. */
    icon?: React.ReactNode;
}

/**
 * Control-tower panel.
 *
 * Square-edged, near-black, lifted by a deep drop shadow rather than a heavy
 * border. The header pairs an optional accent eyebrow with a condensed
 * uppercase title, which is the repeating motif across the design.
 */
export default function Card({
    title,
    description,
    children,
    className = '',
    action,
    footer,
    eyebrow,
    icon,
}: CardProps) {
    return (
        <div
            className={`bg-ink-800 border border-ink-700 shadow-panel transition-colors duration-200 hover:border-accent/40 overflow-hidden ${className}`}
        >
            {(title || action || eyebrow) && (
                <div className="px-6 py-5 border-b border-ink-700 flex items-start justify-between gap-4">
                    <div className="min-w-0">
                        {eyebrow && (
                            <div className="flex items-center gap-1.5 mb-1.5">
                                {icon && <span className="text-accent">{icon}</span>}
                                <span className="eyebrow">{eyebrow}</span>
                            </div>
                        )}
                        {title && (
                            <h3 className="font-heading text-lg font-bold text-white uppercase tracking-tight">
                                {title}
                            </h3>
                        )}
                        {description && (
                            <p className="text-sm text-slate-400 mt-1">{description}</p>
                        )}
                    </div>
                    {action && <div className="shrink-0">{action}</div>}
                </div>
            )}
            <div className="p-6">{children}</div>
            {footer && (
                <div className="px-6 py-4 bg-ink-900 border-t border-ink-700 text-sm text-slate-400">
                    {footer}
                </div>
            )}
        </div>
    );
}
