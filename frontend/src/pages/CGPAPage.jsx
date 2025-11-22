import { useState } from 'react';
import CGPADashboard from '../components/CGPADashboard';

export default function CGPAPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-50 via-white to-navy-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-2">
            <div className="text-4xl">📊</div>
            <h1 className="text-4xl font-bold text-stone-900">
              CGPA Analytics
            </h1>
          </div>
          <p className="text-stone-600 text-lg">
            Track your academic performance and predict your final outcomes
          </p>
        </div>

        {/* CGPA Dashboard Component */}
        <CGPADashboard />

        {/* Info Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Understanding Your CGPA
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
            <div>
              <p className="font-semibold mb-1">Grading Scale (PAU):</p>
              <ul className="space-y-1">
                <li>• A (5.0): 70-100</li>
                <li>• B (4.0): 60-69</li>
                <li>• C (3.0): 50-59</li>
                <li>• D (2.0): 45-49</li>
                <li>• E (1.0): 40-44</li>
                <li>• F (0.0): 0-39</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold mb-1">Degree Classifications:</p>
              <ul className="space-y-1">
                <li>• First Class: 4.50 - 5.00</li>
                <li>• Second Class Upper: 3.50 - 4.49</li>
                <li>• Second Class Lower: 2.50 - 3.49</li>
                <li>• Third Class: 1.50 - 2.49</li>
                <li>• Pass: 1.00 - 1.49</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
