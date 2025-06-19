// src/App.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

const mockLocalStorage = (() => {
    let store: { [key: string]: string } = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => { store[key] = value.toString(); },
        removeItem: (key: string) => { delete store[key]; },
        clear: () => { store = {}; },
        length: 0,
        key: (index: number) => null
    };
})();

beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true
    });
    window.localStorage.clear();
});


test('renders welcome message on home page when not authenticated', () => {
  render(<App />);
  expect(screen.getByText(/Welcome to AlphaDash/i)).toBeInTheDocument();
});

test('shows Login and Register links when not authenticated', () => {
  render(<App />);
  expect(screen.getByRole('link', { name: /Login/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Register/i })).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /My Portfolio/i })).not.toBeInTheDocument();
});

test('shows Portfolio and Manage Assets links when authenticated', () => {
  window.localStorage.setItem('authToken', 'fake-test-token');
  render(<App />);
  expect(screen.getByRole('link', { name: /My Portfolio/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Manage Assets/i })).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: /Login/i })).not.toBeInTheDocument();
});
