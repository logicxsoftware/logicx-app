import { useEffect, useMemo, useState } from 'react'
import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import { BoxesIcon, LayoutDashboardIcon, PackageIcon, PlusIcon } from 'lucide-react'
import { MainWorkspace } from '@codexsun/ui/layouts/main-workspace'
import { MasterForm, MasterListDesk } from '@codexsun/ui/blocks/master-list'
import { productApi, sessionApi } from './api'

const emptyProduct = {
  item: '',
  product_name: '',
  short_description: '',
  description: '',
  enabled: '1',
  collections: '',
  ranking: '0',
  image: '',
  has_variants: '0',
  price: '0',
  compare_at_price: '0',
  opening_stock: '0',
  highlights: '',
}

const productListFields = [
  { id: 'product_name', label: 'Product', required: true },
  { id: 'item_source', label: 'Source' },
  {
    id: 'status',
    label: 'Status',
    options: [
      { label: 'Published', value: 'Published' },
      { label: 'Draft', value: 'Draft' },
    ],
    format: (value) => value || 'Draft',
  },
  { id: 'item_group', label: 'Item group' },
  { id: 'price', label: 'Price', format: (value) => Number(value || 0).toFixed(2) },
  { id: 'modified', label: 'Modified' },
]

const productFields = [
  { id: 'product_name', label: 'Product name', required: true, placeholder: 'Enter the product name' },
  { id: 'short_description', label: 'Short description' },
  { id: 'description', label: 'Description', type: 'textarea' },
  {
    id: 'enabled',
    label: 'Status',
    type: 'select',
    options: [
      { label: 'Published', value: '1' },
      { label: 'Draft', value: '0' },
    ],
  },
  { id: 'collections', label: 'Collections', placeholder: 'Summer, Featured' },
  { id: 'ranking', label: 'Ranking', type: 'number' },
  { id: 'price', label: 'Price', type: 'number' },
  { id: 'compare_at_price', label: 'Compare-at price', type: 'number' },
  { id: 'opening_stock', label: 'Opening stock', type: 'number' },
  { id: 'highlights', label: 'Highlights', type: 'textarea' },
  { id: 'image', label: 'Image URL', showInList: false },
]

function toFormValues(product = {}) {
  return Object.fromEntries(
    Object.keys(emptyProduct).map((field) => [field, String(product[field] ?? emptyProduct[field])]),
  )
}

function toProductPayload(values) {
  return {
    ...values,
    enabled: Number(values.enabled || 0),
    has_variants: Number(values.has_variants || 0),
    ranking: Number(values.ranking || 0),
    price: Number(values.price || 0),
    compare_at_price: Number(values.compare_at_price || 0),
    opening_stock: Number(values.opening_stock || 0),
    image: values.image || null,
  }
}

function ProductsPage() {
  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [error, setError] = useState('')

  async function loadProducts() {
    try {
      setError('')
      setProducts(await productApi.list())
    } catch (exception) {
      setError(exception.message)
    }
  }

  useEffect(() => {
    loadProducts()
  }, [])

  const records = useMemo(
    () =>
      products.map((product) => ({
        ...product,
        id: product.name,
        status: product.enabled ? 'Published' : 'Draft',
      })),
    [products],
  )

  async function removeProduct(product) {
    try {
      await productApi.remove(product.name)
      await loadProducts()
    } catch (exception) {
      setError(exception.message)
    }
  }

  async function suspendProduct(product) {
    try {
      await productApi.update(product.name, { enabled: 0 })
      await loadProducts()
    } catch (exception) {
      setError(exception.message)
    }
  }

  return (
    <div className="flex h-full min-h-full w-full flex-col">
      {error ? <p className="mb-4 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
      <MasterListDesk
        columns={productListFields.map((field) => ({
          id: field.id,
          label: field.label,
          render: (record) => field.format ? field.format(record[field.id], record) : record[field.id] || '—',
        }))}
        filters={productListFields.slice(0, 4).map((field) => ({ id: field.id, label: field.label }))}
        filterPlacement="columns"
        getFilterValue={(record, filterId) => String(record[filterId] ?? '')}
        onDelete={removeProduct}
        onEdit={(product) => navigate(`/products/${encodeURIComponent(product.name)}/edit`)}
        onPrimaryAction={() => navigate('/products/new')}
        onSuspend={suspendProduct}
        primaryActionLabel="Add product"
        records={records}
        title="Products"
        totalLabel={`${records.length} products`}
      />
    </div>
  )
}

function ProductEditor({ mode }) {
  const navigate = useNavigate()
  const { name } = useParams()
  const isEdit = mode === 'edit'
  const isLink = mode === 'link'
  const [values, setValues] = useState(emptyProduct)
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(isEdit || isLink)

  useEffect(() => {
    async function load() {
      try {
        if (isEdit) setValues(toFormValues(await productApi.get(name)))
        if (isLink) {
          const [availableItems, products] = await Promise.all([productApi.items(), productApi.list()])
          const linkedItems = new Set(products.map((product) => product.item))
          setItems(availableItems.filter((item) => !linkedItems.has(item.name)))
        }
      } catch (exception) {
        setError(exception.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [isEdit, isLink, name])

  const fields = useMemo(() => {
    if (!isLink) return productFields
    return [
      {
        id: 'item',
        label: 'ERPNext item',
        required: true,
        type: 'select',
        options: items.map((item) => ({ label: item.item_name || item.name, value: item.name })),
      },
      ...productFields,
    ]
  }, [isLink, items])

  function updateItem(itemName) {
    const item = items.find((entry) => entry.name === itemName)
    if (!item) return
    setValues((current) => ({
      ...current,
      item: item.name,
      product_name: item.item_name || item.name,
      description: item.description || '',
      image: item.image || '',
      price: String(item.standard_rate || 0),
      has_variants: item.has_variants ? '1' : '0',
    }))
  }

  async function save(nextValues) {
    try {
      setError('')
      const payload = toProductPayload(nextValues)
      if (isEdit) await productApi.update(name, payload)
      else if (isLink) await productApi.linkExisting(nextValues.item, payload)
      else await productApi.createNew(payload)
      navigate('/products')
    } catch (exception) {
      setError(exception.message)
    }
  }

  if (loading) return <div className="p-6 text-sm text-muted-foreground">Loading product…</div>

  return (
    <div className="mx-auto w-full max-w-[1100px] p-6">
      {error ? <p className="mb-4 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}
      <MasterForm
        description={isEdit ? 'Update the LogicX product and its ERPNext fields.' : 'Create a LogicX product backed by an ERPNext Item.'}
        fields={fields}
        onCancel={() => navigate('/products')}
        onSubmit={save}
        onValueChange={(field, value) => {
          if (field === 'item') updateItem(value)
          else setValues((current) => ({ ...current, [field]: value }))
        }}
        formId="logicx-product-form"
        submitLabel={isEdit ? 'Update product' : 'Create product'}
        title={isEdit ? 'Edit product' : isLink ? 'Link existing item' : 'New product'}
        values={values}
      />
    </div>
  )
}

export default function LogicXProductWorkspace() {
  const location = useLocation()
  const navigate = useNavigate()
  const [user, setUser] = useState({ email: '', name: 'Administrator', initials: 'A' })

  useEffect(() => {
    sessionApi.currentUser().then((currentUser) => setUser({ ...currentUser, initials: currentUser.fallback })).catch(() => {})
  }, [])

  const navigation = [
    {
      label: 'Workspace',
      items: [
        {
          label: 'Products',
          icon: PackageIcon,
          active: location.pathname.startsWith('/products'),
          onSelect: () => navigate('/products'),
        },
      ],
    },
  ]

  return (
    <MainWorkspace
      applicationIcon={BoxesIcon}
      applicationId="logicx"
      applicationLogoUrl="/assets/logicx_app/images/logicx-logo.svg?v=3"
      applicationName="LogicX"
      defaultFeatures={{ primaryActivityRail: false, secondaryUtilityRail: false }}
      apps={[{ active: true, href: '/logicx-app', icon: BoxesIcon, label: 'LogicX' }]}
      contentClassName="h-full min-h-full overflow-visible"
      navigation={navigation}
      notificationCount={0}
      onSearchChange={() => {}}
      primaryAction={{ icon: PlusIcon, label: 'Add product', onSelect: () => navigate('/products/new') }}
      showTopologyTools={false}
      statusLabel="Connected"
      user={{
        email: user.email,
        initials: user.initials,
        name: user.name,
        onSignOut: async () => {
          await sessionApi.logout()
          window.location.assign('/login?redirect-to=/logicx-app')
        },
      }}
      workspaceTitle="LogicX workspace"
    >
      <Routes>
        <Route path="/" element={<Navigate replace to="/products" />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/products/new" element={<ProductEditor mode="new" />} />
        <Route path="/products/link" element={<ProductEditor mode="link" />} />
        <Route path="/products/:name/edit" element={<ProductEditor mode="edit" />} />
        <Route path="*" element={<Navigate replace to="/products" />} />
      </Routes>
    </MainWorkspace>
  )
}
