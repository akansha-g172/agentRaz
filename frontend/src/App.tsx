import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import AuditPage from './pages/Audit'
import BuyerPage from './pages/Buyer'
import MerchantPage from './pages/Merchant'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<BuyerPage />} />
          <Route path="/merchant" element={<MerchantPage />} />
          <Route path="/audit" element={<AuditPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
