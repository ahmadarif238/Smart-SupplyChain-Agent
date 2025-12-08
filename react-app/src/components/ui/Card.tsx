import React from 'react';

interface CardProps {
    title?: string;
    description?: string;
    children: React.ReactNode;
    className?: string;
    action?: React.ReactNode;
    footer?: React.ReactNode;
}

export default function Card({ title, description, children, className = '', action, footer }: CardProps) {
    return (
        <div className={`bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden ${className}`}>
            {(title || action) && (
                <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
                    <div>
                        {title && <h3 className="text-lg font-semibold text-slate-900">{title}</h3>}
                        {description && <p className="text-sm text-slate-500 mt-1">{description}</p>}
                    </div>
                    {action && <div>{action}</div>}
                </div>
            )}
            <div className="p-6">
                {children}
            </div>
            {footer && (
                <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 text-sm text-slate-500">
                    {footer}
                </div>
            )}
        </div>
    );
}
