import { render, screen } from '@testing-library/react';
import { Header } from '@/components/layout/Header';

describe('Header', () => {
  it('renders the header element', () => {
    render(<Header />);
    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();
  });

  it('renders "ASR Records Legacy" title', () => {
    render(<Header />);
    expect(
      screen.getByRole('heading', { name: /asr records legacy/i })
    ).toBeInTheDocument();
  });

  it('renders tenant badge "ASR Construction"', () => {
    render(<Header />);
    expect(screen.getByText('ASR Construction')).toBeInTheDocument();
  });

  it('renders notifications button', () => {
    render(<Header />);
    expect(
      screen.getByRole('button', { name: /notifications/i })
    ).toBeInTheDocument();
  });

  it('renders notification indicator dot', () => {
    render(<Header />);
    const notifButton = screen.getByRole('button', {
      name: /notifications/i,
    });
    const dot = notifButton.querySelector('.bg-red-500');
    expect(dot).toBeInTheDocument();
  });

  it('renders settings button', () => {
    render(<Header />);
    expect(
      screen.getByRole('button', { name: /settings/i })
    ).toBeInTheDocument();
  });

  it('renders user name "John Doe"', () => {
    render(<Header />);
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('renders user email', () => {
    render(<Header />);
    expect(
      screen.getByText('john.doe@asr-records.com')
    ).toBeInTheDocument();
  });

  it('renders user menu button', () => {
    render(<Header />);
    expect(
      screen.getByRole('button', { name: /user menu/i })
    ).toBeInTheDocument();
  });
});
