import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface PageErrorBoundaryProps {
  children: ReactNode;
  pageName: string;
}

interface PageErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class PageErrorBoundary extends Component<PageErrorBoundaryProps, PageErrorBoundaryState> {
  constructor(props: PageErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): PageErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error(`[${this.props.pageName}] Error boundary caught:`, error, errorInfo);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div role="alert" className="flex flex-col items-center justify-center h-64 text-center">
          <AlertCircle className="h-10 w-10 text-error-400 mb-3" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {this.props.pageName} failed to load
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
            An error occurred while rendering this page.
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mb-4 max-w-md font-mono">
            {this.state.error?.message}
          </p>
          <div className="flex gap-3">
            <button
              onClick={this.handleRetry}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
            >
              <RefreshCw className="h-4 w-4" />
              Try again
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-sm"
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
