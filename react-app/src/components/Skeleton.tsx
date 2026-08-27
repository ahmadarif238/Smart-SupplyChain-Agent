interface SkeletonProps {
    className?: string;
    variant?: 'text' | 'circular' | 'rectangular' | 'card';
    width?: string | number;
    height?: string | number;
    count?: number;
}

export function Skeleton({
    className = '',
    variant = 'rectangular',
    width,
    height,
    count = 1
}: SkeletonProps) {
    const baseClass = "animate-pulse bg-gradient-to-r from-ink-700 via-ink-800 to-ink-700 bg-[length:200%_100%]";

    const variantClasses = {
        text: 'h-4 rounded',
        circular: 'rounded-full',
        rectangular: 'rounded-none',
        card: 'rounded-none'
    };

    const style = {
        width: width || (variant === 'circular' ? '40px' : '100%'),
        height: height || (variant === 'text' ? '16px' : variant === 'circular' ? '40px' : '200px')
    };

    return (
        <>
            {Array.from({ length: count }).map((_, idx) => (
                <div
                    key={idx}
                    className={`${baseClass} ${variantClasses[variant]} ${className}`}
                    style={style}
                />
            ))}
        </>
    );
}

// Card Skeleton
export function CardSkeleton() {
    return (
        <div className="bg-ink-800 rounded-none p-6 border border-ink-700 space-y-4">
            <Skeleton variant="text" width="60%" height={24} />
            <Skeleton variant="rectangular" height={100} />
            <div className="grid grid-cols-3 gap-4">
                <Skeleton variant="rectangular" height={60} />
                <Skeleton variant="rectangular" height={60} />
                <Skeleton variant="rectangular" height={60} />
            </div>
        </div>
    );
}

// Table Skeleton
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="space-y-3">
            <div className="bg-ink-900 rounded-none p-4 grid grid-cols-4 gap-4">
                <Skeleton variant="text" />
                <Skeleton variant="text" />
                <Skeleton variant="text" />
                <Skeleton variant="text" />
            </div>
            {Array.from({ length: rows }).map((_, idx) => (
                <div key={idx} className="bg-ink-800 rounded-none p-4 grid grid-cols-4 gap-4 border border-ink-700">
                    <Skeleton variant="text" />
                    <Skeleton variant="text" />
                    <Skeleton variant="text" />
                    <Skeleton variant="text" />
                </div>
            ))}
        </div>
    );
}

// Chart Skeleton
export function ChartSkeleton() {
    return (
        <div className="bg-ink-800 rounded-none p-6 border border-ink-700">
            <Skeleton variant="text" width="40%" height={20} className="mb-6" />
            <div className="flex items-end justify-between gap-2 h-64">
                {Array.from({ length: 8 }).map((_, idx) => (
                    <Skeleton
                        key={idx}
                        variant="rectangular"
                        height={`${Math.random() * 80 + 20}%`}
                        className="flex-1"
                    />
                ))}
            </div>
        </div>
    );
}

// Dashboard Skeleton
export function DashboardSkeleton() {
    return (
        <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <CardSkeleton />
                <CardSkeleton />
                <CardSkeleton />
                <CardSkeleton />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <ChartSkeleton />
                <ChartSkeleton />
            </div>
        </div>
    );
}
