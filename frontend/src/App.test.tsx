import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App.tsx';

test('renders the access and registration actions', () => {
  render(<App />);
  expect(screen.getByText(/seu espaço, sob controle/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument();
  expect(screen.getAllByRole('button', { name: /criar conta/i }).length).toBeGreaterThan(0);
});
