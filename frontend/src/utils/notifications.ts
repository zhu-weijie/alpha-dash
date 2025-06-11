// src/utils/notifications.ts
import { toast, TypeOptions } from 'react-toastify';

interface ToastOptions {
    autoClose?: number | false;
}

const defaultOptions: ToastOptions = {
    autoClose: 5000,
};

export const showToast = (message: string, type: TypeOptions = 'info', options?: ToastOptions) => {
    toast(message, { ...defaultOptions, ...options, type });
};

export const notifySuccess = (message: string, options?: ToastOptions) => {
    showToast(message, 'success', options);
};

export const notifyError = (message: string, options?: ToastOptions) => {
    showToast(message, 'error', options);
};

export const notifyWarning = (message: string, options?: ToastOptions) => {
    showToast(message, 'warning', options);
};

export const notifyInfo = (message: string, options?: ToastOptions) => {
    showToast(message, 'info', options);
};
