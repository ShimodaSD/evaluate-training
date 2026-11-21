/** Estado vazio com uma única ação que leva direto ao valor. */
export function EmptyWeek({ onAddPlan }: { onAddPlan: () => void }) {
  return (
    <section className="card empty">
      <h2>Comece colando o treino da semana</h2>
      <p>
        Copie cada treino do TrainingPeaks e cole aqui. Depois é só enviar as atividades do relógio
        para ver o quanto você cumpriu do plano.
      </p>
      <button type="button" className="button" onClick={onAddPlan}>
        Colar treino planejado
      </button>
    </section>
  )
}
