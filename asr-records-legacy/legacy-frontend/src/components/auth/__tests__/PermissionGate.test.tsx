import { render, screen } from '@testing-library/react';
import { PermissionGate } from '../PermissionGate';
import { useAuthStore } from '@/stores/auth/authStore';

describe('PermissionGate', () => {
  afterEach(() => {
    useAuthStore.setState({ userInfo: undefined });
  });

  it('renders children when user has matching permission', () => {
    useAuthStore.setState({
      userInfo: {
        authenticated: true,
        permissions: [{ resource: 'documents', actions: ['read', 'create'] }],
      } as any,
    });

    render(
      <PermissionGate resource="documents" action="read">
        <span>Allowed content</span>
      </PermissionGate>,
    );

    expect(screen.getByText('Allowed content')).toBeInTheDocument();
  });

  it('renders fallback when user lacks permission', () => {
    useAuthStore.setState({
      userInfo: {
        authenticated: true,
        permissions: [{ resource: 'documents', actions: ['read'] }],
      } as any,
    });

    render(
      <PermissionGate
        resource="classifications"
        action="classify"
        fallback={<span>No access</span>}
      >
        <span>Secret content</span>
      </PermissionGate>,
    );

    expect(screen.queryByText('Secret content')).not.toBeInTheDocument();
    expect(screen.getByText('No access')).toBeInTheDocument();
  });

  it('renders children when no permissions array (permissive fallback)', () => {
    useAuthStore.setState({
      userInfo: { authenticated: true } as any,
    });

    render(
      <PermissionGate resource="documents" action="delete">
        <span>Permissive content</span>
      </PermissionGate>,
    );

    expect(screen.getByText('Permissive content')).toBeInTheDocument();
  });
});
