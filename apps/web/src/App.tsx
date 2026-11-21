import { ApiStatus } from './components/ApiStatus'

function App() {
  return (
    <main className="app">
      <header>
        <h1>Avaliação de Treinos de Corrida</h1>
        <p>Compare o treino planejado da semana com o que foi realizado.</p>
      </header>
      <ApiStatus />
    </main>
  )
}

export default App
