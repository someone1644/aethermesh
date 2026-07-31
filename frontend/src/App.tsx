import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Header from './components/common/Header'
import Dashboard from './pages/Dashboard'
import Prompt from './pages/Prompt'
import Run from './pages/Run'
import PastRuns from './pages/PastRuns'
import Policy from './pages/Policy'
import About from './pages/About'
import Logs from './pages/Logs'
import Timeline from './pages/Timeline'
import Replay from './pages/Replay'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-[var(--color-bg)]">
        <Header />
        <main className="min-w-0 flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/prompt" element={<Prompt />} />
            <Route path="/run" element={<Run />} />
            <Route path="/runs" element={<PastRuns />} />
            <Route path="/policy" element={<Policy />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/replay" element={<Replay />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
