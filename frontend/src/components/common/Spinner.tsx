// src/components/Common/Spinner.tsx
import React from 'react';
import './Spinner.css';

const Spinner: React.FC<{ size?: number; color?: string; inline?: boolean }> = ({ size = 40, color = '#007bff', inline = false }) => {
    const spinnerStyle: React.CSSProperties = {
        width: size,
        height: size,
        borderTopColor: color,
        borderRightColor: color,
        borderBottomColor: color,
        display: inline ? 'inline-block' : 'block',
        verticalAlign: inline ? 'middle' : undefined,
        margin: inline ? '0 5px 0 0' : '20px auto',
    };
    return (
        <div 
            className="spinner" 
            style={spinnerStyle}
        ></div>
    );
};
export default Spinner;
