import { useState } from 'react'

interface CandidateLookupProps {
  onOpen: (candidateId: string) => void
}

export function CandidateLookup({ onOpen }: CandidateLookupProps) {
  const [candidateId, setCandidateId] = useState('')
  return (
    <section className="candidate-lookup" aria-labelledby="candidate-lookup-heading">
      <div className="section-header">
        <div>
          <p className="label">D1b exact view</p>
          <h2 id="candidate-lookup-heading">Open a Candidate</h2>
        </div>
      </div>
      <form
        className="candidate-lookup-form"
        aria-label="Open Candidate"
        onSubmit={(event) => {
          event.preventDefault()
          const value = candidateId.trim()
          if (value) onOpen(value)
        }}
      >
        <label htmlFor="candidate-id">Candidate ID</label>
        <div className="candidate-lookup-controls">
          <input
            id="candidate-id"
            value={candidateId}
            onChange={(event) => setCandidateId(event.target.value)}
            placeholder="sha256:..."
            autoComplete="off"
          />
          <button type="submit" disabled={!candidateId.trim()}>Open view</button>
        </div>
        <p className="field-hint">The view is read from Core and binds the exact Candidate, evidence, policy revision, and Human disposition.</p>
      </form>
    </section>
  )
}
