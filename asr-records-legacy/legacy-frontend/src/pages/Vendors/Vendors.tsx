import React, { useState, useMemo } from 'react';
import { Search, Plus, Pencil, Trash2, Building2, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from '@/components/common/Button';
import { useVendors, useCreateVendor, useUpdateVendor, useDeleteVendor } from '@/hooks/api/useVendors';
import type { Vendor, VendorCreateRequest } from '@/types/api';

// ---------- Modal wrapper ----------
interface ModalProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}
const Modal: React.FC<ModalProps> = ({ title, onClose, children }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-label={title}>
    <div className="fixed inset-0 bg-black/50" onClick={onClose} />
    <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300" aria-label="Close">
          <X className="h-5 w-5" />
        </button>
      </div>
      {children}
    </div>
  </div>
);

// ---------- Vendor form ----------
interface VendorFormValues {
  name: string;
  display_name: string;
  email: string;
  phone: string;
  notes: string;
}

const emptyForm: VendorFormValues = { name: '', display_name: '', email: '', phone: '', notes: '' };

function vendorToForm(v: Vendor): VendorFormValues {
  return {
    name: v.name,
    display_name: v.display_name || '',
    email: v.contact_info?.email || '',
    phone: v.contact_info?.phone || '',
    notes: v.notes || '',
  };
}

interface VendorFormProps {
  initial?: VendorFormValues;
  submitLabel: string;
  onSubmit: (values: VendorFormValues) => void;
  onCancel: () => void;
  isPending: boolean;
}
const VendorForm: React.FC<VendorFormProps> = ({ initial = emptyForm, submitLabel, onSubmit, onCancel, isPending }) => {
  const [values, setValues] = useState<VendorFormValues>(initial);
  const set = (k: keyof VendorFormValues) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setValues((p) => ({ ...p, [k]: e.target.value }));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(values);
      }}
      className="space-y-4"
    >
      <div>
        <label htmlFor="vendor-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
        <input id="vendor-name" className="input" required value={values.name} onChange={set('name')} placeholder="Vendor name" />
      </div>
      <div>
        <label htmlFor="vendor-display-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Display Name</label>
        <input id="vendor-display-name" className="input" value={values.display_name} onChange={set('display_name')} placeholder="Optional display name" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="vendor-email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
          <input id="vendor-email" type="email" className="input" value={values.email} onChange={set('email')} placeholder="email@example.com" />
        </div>
        <div>
          <label htmlFor="vendor-phone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
          <input id="vendor-phone" className="input" value={values.phone} onChange={set('phone')} placeholder="555-1234" />
        </div>
      </div>
      <div>
        <label htmlFor="vendor-notes" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
        <textarea id="vendor-notes" className="input" rows={2} value={values.notes} onChange={set('notes')} placeholder="Optional notes" />
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onCancel} type="button">Cancel</Button>
        <Button type="submit" disabled={isPending || !values.name.trim()}>{isPending ? 'Saving...' : submitLabel}</Button>
      </div>
    </form>
  );
};

// ---------- Page ----------
export const Vendors: React.FC = () => {
  const { data: vendors = [], isLoading } = useVendors();
  const createMutation = useCreateVendor();
  const updateMutation = useUpdateVendor();
  const deleteMutation = useDeleteVendor();

  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const filteredVendors = useMemo(() => {
    if (!searchQuery.trim()) return vendors;
    const q = searchQuery.toLowerCase();
    return vendors.filter(
      (v: Vendor) =>
        v.name.toLowerCase().includes(q) ||
        (v.display_name || '').toLowerCase().includes(q) ||
        (v.notes || '').toLowerCase().includes(q),
    );
  }, [vendors, searchQuery]);

  const handleCreate = (values: VendorFormValues) => {
    const payload: VendorCreateRequest = {
      name: values.name,
      display_name: values.display_name || undefined,
      tenant_id: 'default',
      contact_info: values.email || values.phone ? { email: values.email || undefined, phone: values.phone || undefined } : undefined,
      notes: values.notes || undefined,
    };
    createMutation.mutate(payload, {
      onSuccess: () => setShowAddModal(false),
    });
  };

  const handleUpdate = (values: VendorFormValues) => {
    if (!editingVendor) return;
    updateMutation.mutate(
      {
        id: editingVendor.id,
        vendor: {
          name: values.name,
          display_name: values.display_name || undefined,
          contact_info: { email: values.email || undefined, phone: values.phone || undefined },
          notes: values.notes || undefined,
        },
      },
      { onSuccess: () => setEditingVendor(null) },
    );
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => setConfirmDeleteId(null),
      onError: () => {
        toast.error('Failed to delete vendor');
        setConfirmDeleteId(null);
      },
    });
  };

  const renderLoading = () => (
    <div className="p-6 animate-pulse space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex space-x-4">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6"></div>
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
        </div>
      ))}
    </div>
  );

  const renderEmpty = () => (
    <div className="p-12 text-center">
      <Building2 className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No vendors found</h3>
      <p className="text-gray-500 dark:text-gray-400">
        {searchQuery ? `No vendors match "${searchQuery}".` : 'Add your first vendor to start tracking.'}
      </p>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Vendors</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Manage vendors and view their document processing statistics.
        </p>
      </div>

      {/* Search + Add */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search vendors..."
              className="input pl-10"
              aria-label="Search vendors"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setShowAddModal(true)}>
            Add Vendor
          </Button>
        </div>
      </div>

      {/* Vendors Table */}
      <div className="card overflow-hidden">
        {isLoading && renderLoading()}
        {!isLoading && filteredVendors.length === 0 && renderEmpty()}
        {!isLoading && filteredVendors.length > 0 && (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Documents</th>
                  <th className="hidden md:table-cell">Total Processed</th>
                  <th className="hidden md:table-cell">Avg Amount</th>
                  <th className="hidden md:table-cell">Last Invoice</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filteredVendors.map((v: Vendor) => (
                  <tr key={v.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td>
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
                          <Building2 className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-gray-100">{v.name}</div>
                          {v.display_name && v.display_name !== v.name && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">{v.display_name}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{v.document_count}</span>
                    </td>
                    <td className="hidden md:table-cell">
                      <span className="text-sm text-gray-900 dark:text-gray-100">
                        ${v.total_amount_processed?.toLocaleString() || '0'}
                      </span>
                    </td>
                    <td className="hidden md:table-cell">
                      <span className="text-sm text-gray-900 dark:text-gray-100">
                        ${v.average_amount?.toLocaleString() || '0'}
                      </span>
                    </td>
                    <td className="hidden md:table-cell">
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {v.last_document_date ? new Date(v.last_document_date).toLocaleDateString() : '--'}
                      </span>
                    </td>
                    <td>
                      <div className="flex space-x-1">
                        <Button variant="ghost" size="sm" onClick={() => setEditingVendor(v)} aria-label={`Edit ${v.name}`}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        {confirmDeleteId === v.id ? (
                          <span className="inline-flex items-center gap-1 text-xs">
                            <span className="text-gray-600 dark:text-gray-400">Delete?</span>
                            <Button variant="ghost" size="sm" onClick={() => handleDelete(v.id)} className="text-red-600 hover:text-red-700" disabled={deleteMutation.isPending}>
                              Yes
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => setConfirmDeleteId(null)}>
                              No
                            </Button>
                          </span>
                        ) : (
                          <Button variant="ghost" size="sm" onClick={() => setConfirmDeleteId(v.id)} className="text-red-600 hover:text-red-700" aria-label={`Delete ${v.name}`}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{vendors.length}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Vendors</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {vendors.reduce((sum: number, v: Vendor) => sum + v.document_count, 0)}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Documents</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            ${(vendors.reduce((sum: number, v: Vendor) => sum + (v.total_amount_processed || 0), 0) / 1000).toFixed(1)}K
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Processed</div>
        </div>
      </div>

      {/* Add Vendor Modal */}
      {showAddModal && (
        <Modal title="Add Vendor" onClose={() => setShowAddModal(false)}>
          <VendorForm submitLabel="Add Vendor" onSubmit={handleCreate} onCancel={() => setShowAddModal(false)} isPending={createMutation.isPending} />
        </Modal>
      )}

      {/* Edit Vendor Modal */}
      {editingVendor && (
        <Modal title="Edit Vendor" onClose={() => setEditingVendor(null)}>
          <VendorForm
            initial={vendorToForm(editingVendor)}
            submitLabel="Save Changes"
            onSubmit={handleUpdate}
            onCancel={() => setEditingVendor(null)}
            isPending={updateMutation.isPending}
          />
        </Modal>
      )}
    </div>
  );
};
