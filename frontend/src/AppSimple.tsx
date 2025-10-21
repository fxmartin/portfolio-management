import { useState } from 'react'

function AppSimple() {
  const [count, setCount] = useState(0)

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Portfolio Management - Test</h1>
      <p>If you can see this, React is working!</p>
      <button onClick={() => setCount(count + 1)}>
        Count: {count}
      </button>
      <hr />
      <p>Now testing the Import button...</p>
      <button onClick={() => alert('Import clicked!')}>
        Import Transactions
      </button>
    </div>
  )
}

export default AppSimple