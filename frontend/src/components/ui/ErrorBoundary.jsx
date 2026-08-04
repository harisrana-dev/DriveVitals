import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('[error-boundary] Caught a render error:', error, info.componentStack);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="ui-error-boundary" role="alert">
          <div className="ui-error-boundary__title">Something went wrong.</div>
          <p className="ui-error-boundary__description">
            The application hit an unexpected error. Reload to try again.
          </p>
          <button type="button" className="ui-error-boundary__action" onClick={this.handleReload}>
            Reload page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
