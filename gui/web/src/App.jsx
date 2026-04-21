import { useEffect, useRef, useState } from 'react'

const KEYS = ['W', 'A', 'S', 'D', 'Q', 'E']
const BRIDGE_URL = 'http://localhost:8000/command'

function sendCommand(cmd) {
  fetch(BRIDGE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cmd }),
  }).catch((err) => console.error('bridge error', err))
}

export default function App() {
  const [pressed, setPressed] = useState(new Set())
  const pressedRef = useRef(new Set())

  useEffect(() => {
    const onDown = (e) => {
      const k = e.key.toUpperCase()
      if (!KEYS.includes(k)) return
      if (pressedRef.current.has(k)) return // ignore auto-repeat
      pressedRef.current.add(k)
      setPressed(new Set(pressedRef.current))
      sendCommand(k)
    }
    const onUp = (e) => {
      const k = e.key.toUpperCase()
      if (!KEYS.includes(k)) return
      pressedRef.current.delete(k)
      setPressed(new Set(pressedRef.current))
      if (pressedRef.current.size > 0) {
        // another WASD key still held — re-send it so motion continues
        const remaining = Array.from(pressedRef.current).pop()
        sendCommand(remaining)
      } else {
        sendCommand('STOP')
      }
    }
    window.addEventListener('keydown', onDown)
    window.addEventListener('keyup', onUp)
    return () => {
      window.removeEventListener('keydown', onDown)
      window.removeEventListener('keyup', onUp)
    }
  }, [])

  return (
    <div className="wrap">
      <h1>Pacbot Drive</h1>
      <p className="hint">WASD to drive, Q/E to rotate. Release to stop.</p>
      <div className="keys">
        <div className="row">
          <Key label="Q" active={pressed.has('Q')} />
          <Key label="W" active={pressed.has('W')} />
          <Key label="E" active={pressed.has('E')} />
        </div>
        <div className="row">
          <Key label="A" active={pressed.has('A')} />
          <Key label="S" active={pressed.has('S')} />
          <Key label="D" active={pressed.has('D')} />
        </div>
      </div>
    </div>
  )
}

function Key({ label, active }) {
  return <div className={`key ${active ? 'active' : ''}`}>{label}</div>
}
