import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Navigation } from '@/components/layout/Navigation';

const renderNavigation = (initialEntries = ['/dashboard']) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Navigation />
    </MemoryRouter>
  );
};

/**
 * Helper to find a nav link by its label text.
 * Uses the link role to avoid ambiguity with stat labels and wrapper elements.
 */
const getNavLink = (name: string): HTMLAnchorElement => {
  const links = screen.getAllByRole('link');
  const match = links.find((link) => {
    const span = link.querySelector(':scope > div > div > span');
    return span?.textContent === name;
  });
  if (!match) {
    throw new Error(`Could not find nav link with label "${name}"`);
  }
  return match as HTMLAnchorElement;
};

describe('Navigation', () => {
  // --- Branding ---

  it('renders ASR Records brand name', () => {
    renderNavigation();
    expect(
      screen.getByRole('heading', { name: /asr records/i })
    ).toBeInTheDocument();
  });

  it('renders Legacy Edition subtitle', () => {
    renderNavigation();
    expect(screen.getByText('Legacy Edition')).toBeInTheDocument();
  });

  // --- Quick stats ---

  it('renders document count stat "1,234"', () => {
    renderNavigation();
    expect(screen.getByText('1,234')).toBeInTheDocument();
  });

  it('renders accuracy stat "94%"', () => {
    renderNavigation();
    expect(screen.getByText('94%')).toBeInTheDocument();
  });

  // --- Primary nav links ---

  it('renders Dashboard nav link', () => {
    renderNavigation();
    const link = getNavLink('Dashboard');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/dashboard');
  });

  it('renders Upload nav link', () => {
    renderNavigation();
    const link = getNavLink('Upload');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/upload');
  });

  it('renders Documents nav link', () => {
    renderNavigation();
    const link = getNavLink('Documents');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/documents');
  });

  // --- Secondary nav links ---

  it('renders Reports nav link', () => {
    renderNavigation();
    const link = getNavLink('Reports');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/reports');
  });

  it('renders Settings nav link', () => {
    renderNavigation();
    const link = getNavLink('Settings');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/settings');
  });

  // --- Active state ---

  it('highlights active Dashboard link when on /dashboard', () => {
    renderNavigation(['/dashboard']);
    const dashboardLink = getNavLink('Dashboard');
    expect(dashboardLink).toBeInTheDocument();
    expect(dashboardLink.className).toContain('bg-primary-50');
  });

  it('highlights active Documents link when on /documents', () => {
    renderNavigation(['/documents']);
    const documentsLink = getNavLink('Documents');
    expect(documentsLink).toBeInTheDocument();
    expect(documentsLink.className).toContain('bg-primary-50');
  });

  // --- Footer ---

  it('renders System Online status', () => {
    renderNavigation();
    expect(screen.getByText('System Online')).toBeInTheDocument();
  });

  it('renders last sync time', () => {
    renderNavigation();
    expect(
      screen.getByText('Last sync: 2 minutes ago')
    ).toBeInTheDocument();
  });
});
