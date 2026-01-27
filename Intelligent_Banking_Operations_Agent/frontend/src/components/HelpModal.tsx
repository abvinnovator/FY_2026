import React from 'react';
import Button from './Button';

interface HelpModalProps {
  onClose: () => void;
}

const HelpModal: React.FC<HelpModalProps> = ({ onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-neutral-900 border border-border/60 rounded-lg p-6 max-w-lg w-full shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold">About This App</h2>
        <p className="text-gray-300 mt-2 text-sm">
          This application is a demonstration of an Intelligent Banking Operations Agent. It uses a multi-agent system built with LangGraph to triage financial tasks.
        </p>
        <ul className="list-disc pl-5 mt-4 text-sm space-y-1 text-gray-400">
          <li><strong>Fraud Triage:</strong> Analyzes transaction data to detect and flag potentially fraudulent activities.</li>
          <li><strong>Credit Triage:</strong> Assesses credit applications based on income, liabilities, and other factors.</li>
          <li><strong>Analytics:</strong> Displays key performance indicators related to the agent's operations.</li>
        </ul>
        <p className="text-gray-300 mt-4 text-sm">
          The frontend is built with React, TypeScript, and Vite, and the backend is powered by FastAPI and Python.
        </p>
        <div className="mt-6 flex justify-end">
          <Button onClick={onClose}>Close</Button>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
