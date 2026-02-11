import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/common/Button';
import type { DocumentFilters } from '@/types/api';

interface FilterPanelProps {
  onApply: (filters: DocumentFilters) => void;
  onClose: () => void;
  currentFilters: DocumentFilters;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({ onApply, onClose, currentFilters }) => {
  const [dateStart, setDateStart] = useState(currentFilters.date_range?.start || '');
  const [dateEnd, setDateEnd] = useState(currentFilters.date_range?.end || '');
  const [minAmount, setMinAmount] = useState(currentFilters.amount_range?.min?.toString() || '');
  const [maxAmount, setMaxAmount] = useState(currentFilters.amount_range?.max?.toString() || '');
  const [vendor, setVendor] = useState(currentFilters.vendor || '');
  const [paymentStatus, setPaymentStatus] = useState<string>(
    currentFilters.payment_status?.[0] || ''
  );

  const handleApply = () => {
    const filters: DocumentFilters = {};

    if (dateStart || dateEnd) {
      filters.date_range = {
        start: dateStart,
        end: dateEnd,
        field: 'created_at',
      };
    }

    if (minAmount || maxAmount) {
      filters.amount_range = {
        min: minAmount ? Number(minAmount) : 0,
        max: maxAmount ? Number(maxAmount) : Number.MAX_SAFE_INTEGER,
      };
    }

    if (vendor) {
      filters.vendor = vendor;
    }

    if (paymentStatus) {
      filters.payment_status = [paymentStatus as any];
    }

    onApply(filters);
  };

  const handleClear = () => {
    setDateStart('');
    setDateEnd('');
    setMinAmount('');
    setMaxAmount('');
    setVendor('');
    setPaymentStatus('');
    onApply({});
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-gray-700">Filters</h4>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Date Range */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Date From</label>
          <input
            type="date"
            className="input text-sm"
            value={dateStart}
            onChange={(e) => setDateStart(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Date To</label>
          <input
            type="date"
            className="input text-sm"
            value={dateEnd}
            onChange={(e) => setDateEnd(e.target.value)}
          />
        </div>

        {/* Vendor */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Vendor</label>
          <input
            type="text"
            className="input text-sm"
            placeholder="Filter by vendor..."
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
          />
        </div>

        {/* Amount Range */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Min Amount ($)</label>
          <input
            type="number"
            className="input text-sm"
            placeholder="0"
            value={minAmount}
            onChange={(e) => setMinAmount(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Max Amount ($)</label>
          <input
            type="number"
            className="input text-sm"
            placeholder="No limit"
            value={maxAmount}
            onChange={(e) => setMaxAmount(e.target.value)}
          />
        </div>

        {/* Payment Status */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Payment Status</label>
          <select
            className="input text-sm"
            value={paymentStatus}
            onChange={(e) => setPaymentStatus(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="paid">Paid</option>
            <option value="unpaid">Unpaid</option>
            <option value="partial">Partial</option>
            <option value="void">Void</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end space-x-2 mt-4">
        <Button variant="ghost" size="sm" onClick={handleClear}>
          Clear All
        </Button>
        <Button variant="primary" size="sm" onClick={handleApply}>
          Apply Filters
        </Button>
      </div>
    </div>
  );
};
