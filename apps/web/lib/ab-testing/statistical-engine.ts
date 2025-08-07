// Statistical Analysis Engine for A/B Testing
// Rigorous statistical calculations with automated decision making

export interface StatisticalResult {
  experimentId: string
  variantId: string
  metric: string
  sampleSize: number
  conversionRate: number
  confidenceInterval: [number, number]
  pValue: number
  statisticalSignificance: boolean
  practicalSignificance: boolean
  zScore: number
  standardError: number
  liftPercent: number
  recommendedAction: 'continue' | 'ship' | 'kill' | 'extend'
  riskAssessment: 'low' | 'medium' | 'high'
}

export interface ExperimentResults {
  experimentId: string
  experimentName: string
  status: 'running' | 'completed' | 'stopped'
  startDate: Date
  endDate?: Date
  controlVariant: string
  variants: StatisticalResult[]
  winner?: string
  confidence: number
  recommendations: string[]
  riskFactors: string[]
  nextSteps: string[]
}

export interface BayesianResult {
  experimentId: string
  variantId: string
  posteriorMean: number
  posteriorStd: number
  probabilityToBeat: number
  expectedLoss: number
  credibleInterval: [number, number]
}

// Statistical analysis class
export class StatisticalEngine {
  private static instance: StatisticalEngine
  private readonly MIN_SAMPLE_SIZE = 100
  private readonly SIGNIFICANCE_THRESHOLD = 0.05
  private readonly PRACTICAL_SIGNIFICANCE_THRESHOLD = 0.02 // 2% minimum improvement
  private readonly MAX_EXPERIMENT_RUNTIME = 28 // days

  static getInstance(): StatisticalEngine {
    if (!StatisticalEngine.instance) {
      StatisticalEngine.instance = new StatisticalEngine()
    }
    return StatisticalEngine.instance
  }

  // Analyze A/B test results using frequentist statistics
  analyzeExperiment(
    experimentId: string,
    controlData: { conversions: number; visitors: number },
    variantData: Array<{ id: string; conversions: number; visitors: number }>,
    metric: string = 'conversion_rate',
    alpha: number = 0.05
  ): ExperimentResults {
    const results: StatisticalResult[] = []
    const controlRate = controlData.conversions / controlData.visitors

    // Analyze each variant against control
    variantData.forEach(variant => {
      const variantRate = variant.conversions / variant.visitors
      const result = this.performTTest(
        controlData,
        { conversions: variant.conversions, visitors: variant.visitors },
        variant.id,
        experimentId,
        metric,
        alpha
      )
      results.push(result)
    })

    // Determine winner and recommendations
    const winner = this.determineWinner(results, controlRate)
    const recommendations = this.generateRecommendations(results, controlRate)
    const riskFactors = this.assessRiskFactors(results)
    const nextSteps = this.generateNextSteps(results, winner)

    return {
      experimentId,
      experimentName: `Experiment ${experimentId}`,
      status: this.determineExperimentStatus(results),
      startDate: new Date(), // This should come from experiment config
      controlVariant: 'control',
      variants: results,
      winner,
      confidence: Math.max(...results.map(r => (1 - r.pValue) * 100)),
      recommendations,
      riskFactors,
      nextSteps
    }
  }

  // Perform two-proportion z-test
  private performTTest(
    control: { conversions: number; visitors: number },
    variant: { conversions: number; visitors: number },
    variantId: string,
    experimentId: string,
    metric: string,
    alpha: number
  ): StatisticalResult {
    const p1 = control.conversions / control.visitors
    const p2 = variant.conversions / variant.visitors
    const n1 = control.visitors
    const n2 = variant.visitors

    // Pooled proportion
    const pooledP = (control.conversions + variant.conversions) / (n1 + n2)
    
    // Standard error
    const se = Math.sqrt(pooledP * (1 - pooledP) * (1/n1 + 1/n2))
    
    // Z-score
    const zScore = (p2 - p1) / se
    
    // P-value (two-tailed test)
    const pValue = 2 * (1 - this.normalCDF(Math.abs(zScore)))
    
    // Confidence interval for difference
    const criticalValue = this.inverseNormalCDF(1 - alpha/2)
    const marginError = criticalValue * se
    const lowerBound = (p2 - p1) - marginError
    const upperBound = (p2 - p1) + marginError
    
    // Statistical and practical significance
    const statisticalSignificance = pValue < alpha && variant.visitors >= this.MIN_SAMPLE_SIZE
    const liftPercent = ((p2 - p1) / p1) * 100
    const practicalSignificance = Math.abs(liftPercent) >= this.PRACTICAL_SIGNIFICANCE_THRESHOLD * 100

    return {
      experimentId,
      variantId,
      metric,
      sampleSize: n2,
      conversionRate: p2 * 100,
      confidenceInterval: [lowerBound * 100, upperBound * 100],
      pValue,
      statisticalSignificance,
      practicalSignificance,
      zScore,
      standardError: se,
      liftPercent,
      recommendedAction: this.getRecommendedAction(
        pValue, 
        liftPercent, 
        n2, 
        statisticalSignificance, 
        practicalSignificance
      ),
      riskAssessment: this.assessRisk(pValue, liftPercent, n2)
    }
  }

  // Bayesian analysis for continuous monitoring
  performBayesianAnalysis(
    controlData: { conversions: number; visitors: number },
    variantData: { conversions: number; visitors: number },
    variantId: string,
    experimentId: string,
    priorAlpha: number = 1,
    priorBeta: number = 1
  ): BayesianResult {
    // Beta-Binomial conjugate prior
    const controlPosteriorAlpha = priorAlpha + controlData.conversions
    const controlPosteriorBeta = priorBeta + controlData.visitors - controlData.conversions
    
    const variantPosteriorAlpha = priorAlpha + variantData.conversions
    const variantPosteriorBeta = priorBeta + variantData.visitors - variantData.conversions
    
    // Posterior means
    const controlMean = controlPosteriorAlpha / (controlPosteriorAlpha + controlPosteriorBeta)
    const variantMean = variantPosteriorAlpha / (variantPosteriorAlpha + variantPosteriorBeta)
    
    // Posterior standard deviations
    const variantStd = Math.sqrt(
      (variantPosteriorAlpha * variantPosteriorBeta) /
      (Math.pow(variantPosteriorAlpha + variantPosteriorBeta, 2) * 
       (variantPosteriorAlpha + variantPosteriorBeta + 1))
    )
    
    // Probability that variant beats control (Monte Carlo approximation)
    const probabilityToBeat = this.calculateProbabilityToBeat(
      { alpha: controlPosteriorAlpha, beta: controlPosteriorBeta },
      { alpha: variantPosteriorAlpha, beta: variantPosteriorBeta }
    )
    
    // Expected loss calculation
    const expectedLoss = this.calculateExpectedLoss(
      { alpha: controlPosteriorAlpha, beta: controlPosteriorBeta },
      { alpha: variantPosteriorAlpha, beta: variantPosteriorBeta }
    )
    
    // 95% Credible interval
    const credibleInterval = this.calculateCredibleInterval(
      variantPosteriorAlpha,
      variantPosteriorBeta,
      0.95
    )

    return {
      experimentId,
      variantId,
      posteriorMean: variantMean,
      posteriorStd: variantStd,
      probabilityToBeat,
      expectedLoss,
      credibleInterval
    }
  }

  // Sequential testing with alpha spending
  performSequentialAnalysis(
    data: Array<{ conversions: number; visitors: number; timestamp: Date }>,
    alpha: number = 0.05,
    beta: number = 0.2
  ): { shouldStop: boolean; reason: string; confidence: number } {
    // O'Brien-Fleming alpha spending function
    const currentLooks = data.length
    const plannedLooks = 10 // Maximum number of interim analyses
    
    const alphaSpent = this.obfAlphaSpending(currentLooks / plannedLooks, alpha)
    const currentAlpha = currentLooks === 1 ? alphaSpent : 
                        alphaSpent - this.obfAlphaSpending((currentLooks - 1) / plannedLooks, alpha)
    
    // Current test statistics
    const latest = data[data.length - 1]
    const control = data[0] // Assuming first data point is control
    
    const result = this.performTTest(
      control,
      latest,
      'variant',
      'sequential',
      'conversion_rate',
      currentAlpha
    )
    
    // Stopping rules
    if (result.statisticalSignificance && result.practicalSignificance) {
      return {
        shouldStop: true,
        reason: 'Significant positive result detected',
        confidence: (1 - result.pValue) * 100
      }
    }
    
    if (result.liftPercent < -10) { // 10% degradation threshold
      return {
        shouldStop: true,
        reason: 'Significant negative impact detected - safety stop',
        confidence: (1 - result.pValue) * 100
      }
    }
    
    if (currentLooks >= plannedLooks) {
      return {
        shouldStop: true,
        reason: 'Maximum analysis points reached',
        confidence: (1 - result.pValue) * 100
      }
    }
    
    return {
      shouldStop: false,
      reason: 'Continue collecting data',
      confidence: (1 - result.pValue) * 100
    }
  }

  // Multi-armed bandit optimization
  calculateBanditRecommendations(
    variantPerformance: Array<{ id: string; conversions: number; visitors: number }>,
    strategy: 'epsilon-greedy' | 'thompson-sampling' | 'ucb' = 'thompson-sampling'
  ): Record<string, number> {
    const recommendations: Record<string, number> = {}
    
    switch (strategy) {
      case 'thompson-sampling':
        return this.thompsonSampling(variantPerformance)
      
      case 'epsilon-greedy':
        return this.epsilonGreedy(variantPerformance, 0.1)
      
      case 'ucb':
        return this.upperConfidenceBound(variantPerformance)
      
      default:
        return this.thompsonSampling(variantPerformance)
    }
  }

  // Helper methods for statistical calculations

  private normalCDF(x: number): number {
    return (1 + this.erf(x / Math.sqrt(2))) / 2
  }

  private erf(x: number): number {
    // Approximation of error function
    const a1 = 0.254829592
    const a2 = -0.284496736
    const a3 = 1.421413741
    const a4 = -1.453152027
    const a5 = 1.061405429
    const p = 0.3275911
    
    const sign = x >= 0 ? 1 : -1
    x = Math.abs(x)
    
    const t = 1.0 / (1.0 + p * x)
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x)
    
    return sign * y
  }

  private inverseNormalCDF(p: number): number {
    // Beasley-Springer-Moro algorithm
    const a0 = -3.969683028665376e+01
    const a1 = 2.209460984245205e+02
    const a2 = -2.759285104469687e+02
    const a3 = 1.383577518672690e+02
    const a4 = -3.066479806614716e+01
    const a5 = 2.506628277459239e+00
    
    const b1 = -5.447609879822406e+01
    const b2 = 1.615858368580409e+02
    const b3 = -1.556989798598866e+02
    const b4 = 6.680131188771972e+01
    const b5 = -1.328068155288572e+01
    
    if (p < 0.5) {
      const q = Math.sqrt(-2 * Math.log(p))
      return (((((a5 * q + a4) * q + a3) * q + a2) * q + a1) * q + a0) /
             ((((b5 * q + b4) * q + b3) * q + b2) * q + b1)
    } else {
      const q = Math.sqrt(-2 * Math.log(1 - p))
      return -(((((a5 * q + a4) * q + a3) * q + a2) * q + a1) * q + a0) /
              ((((b5 * q + b4) * q + b3) * q + b2) * q + b1)
    }
  }

  private calculateProbabilityToBeat(
    control: { alpha: number; beta: number },
    variant: { alpha: number; beta: number }
  ): number {
    // Monte Carlo simulation
    const simulations = 10000
    let wins = 0
    
    for (let i = 0; i < simulations; i++) {
      const controlSample = this.betaSample(control.alpha, control.beta)
      const variantSample = this.betaSample(variant.alpha, variant.beta)
      
      if (variantSample > controlSample) {
        wins++
      }
    }
    
    return wins / simulations
  }

  private calculateExpectedLoss(
    control: { alpha: number; beta: number },
    variant: { alpha: number; beta: number }
  ): number {
    // Simplified expected loss calculation
    const controlMean = control.alpha / (control.alpha + control.beta)
    const variantMean = variant.alpha / (variant.alpha + variant.beta)
    
    return Math.max(0, controlMean - variantMean)
  }

  private calculateCredibleInterval(
    alpha: number,
    beta: number,
    confidence: number
  ): [number, number] {
    // Approximate credible interval for Beta distribution
    const mean = alpha / (alpha + beta)
    const variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
    const std = Math.sqrt(variance)
    
    const z = this.inverseNormalCDF((1 + confidence) / 2)
    
    return [
      Math.max(0, mean - z * std),
      Math.min(1, mean + z * std)
    ]
  }

  private betaSample(alpha: number, beta: number): number {
    // Box-Muller transformation for Beta distribution sampling
    const u1 = Math.random()
    const u2 = Math.random()
    
    // Using gamma sampling approximation
    const x = Math.pow(u1, 1 / alpha)
    const y = Math.pow(u2, 1 / beta)
    
    return x / (x + y)
  }

  private obfAlphaSpending(t: number, alpha: number): number {
    // O'Brien-Fleming alpha spending function
    if (t <= 0) return 0
    if (t >= 1) return alpha
    
    return 2 * (1 - this.normalCDF(this.inverseNormalCDF(1 - alpha/2) / Math.sqrt(t)))
  }

  private thompsonSampling(
    variants: Array<{ id: string; conversions: number; visitors: number }>
  ): Record<string, number> {
    const samples: Record<string, number> = {}
    
    variants.forEach(variant => {
      const alpha = 1 + variant.conversions
      const beta = 1 + variant.visitors - variant.conversions
      samples[variant.id] = this.betaSample(alpha, beta)
    })
    
    return samples
  }

  private epsilonGreedy(
    variants: Array<{ id: string; conversions: number; visitors: number }>,
    epsilon: number
  ): Record<string, number> {
    const rates: Record<string, number> = {}
    
    variants.forEach(variant => {
      const rate = variant.visitors > 0 ? variant.conversions / variant.visitors : 0
      rates[variant.id] = rate
    })
    
    return rates
  }

  private upperConfidenceBound(
    variants: Array<{ id: string; conversions: number; visitors: number }>
  ): Record<string, number> {
    const totalVisitors = variants.reduce((sum, v) => sum + v.visitors, 0)
    const ucbValues: Record<string, number> = {}
    
    variants.forEach(variant => {
      const rate = variant.visitors > 0 ? variant.conversions / variant.visitors : 0
      const confidence = Math.sqrt((2 * Math.log(totalVisitors)) / variant.visitors)
      ucbValues[variant.id] = rate + confidence
    })
    
    return ucbValues
  }

  private getRecommendedAction(
    pValue: number,
    liftPercent: number,
    sampleSize: number,
    statSig: boolean,
    practSig: boolean
  ): 'continue' | 'ship' | 'kill' | 'extend' {
    if (sampleSize < this.MIN_SAMPLE_SIZE) return 'continue'
    if (statSig && practSig && liftPercent > 0) return 'ship'
    if (statSig && liftPercent < -5) return 'kill' // 5% degradation threshold
    if (sampleSize > 5000 && !statSig) return 'extend'
    return 'continue'
  }

  private assessRisk(pValue: number, liftPercent: number, sampleSize: number): 'low' | 'medium' | 'high' {
    if (sampleSize < this.MIN_SAMPLE_SIZE) return 'high'
    if (pValue < 0.01 && Math.abs(liftPercent) > 5) return 'low'
    if (pValue < 0.05 && Math.abs(liftPercent) > 2) return 'medium'
    return 'high'
  }

  private determineWinner(results: StatisticalResult[], controlRate: number): string | undefined {
    const significantResults = results.filter(r => 
      r.statisticalSignificance && 
      r.practicalSignificance && 
      r.liftPercent > 0
    )
    
    if (significantResults.length === 0) return undefined
    
    // Return variant with highest lift
    return significantResults.reduce((best, current) => 
      current.liftPercent > best.liftPercent ? current : best
    ).variantId
  }

  private generateRecommendations(results: StatisticalResult[], controlRate: number): string[] {
    const recommendations: string[] = []
    
    const winner = results.find(r => r.statisticalSignificance && r.practicalSignificance && r.liftPercent > 0)
    if (winner) {
      recommendations.push(`Ship variant ${winner.variantId} - shows ${winner.liftPercent.toFixed(1)}% improvement`)
    }
    
    const losers = results.filter(r => r.statisticalSignificance && r.liftPercent < -2)
    if (losers.length > 0) {
      recommendations.push(`Kill variants: ${losers.map(r => r.variantId).join(', ')} - showing negative impact`)
    }
    
    const needMoreData = results.filter(r => r.sampleSize < this.MIN_SAMPLE_SIZE * 2)
    if (needMoreData.length > 0 && !winner) {
      recommendations.push(`Continue collecting data for variants: ${needMoreData.map(r => r.variantId).join(', ')}`)
    }
    
    return recommendations
  }

  private assessRiskFactors(results: StatisticalResult[]): string[] {
    const risks: string[] = []
    
    const smallSamples = results.filter(r => r.sampleSize < this.MIN_SAMPLE_SIZE)
    if (smallSamples.length > 0) {
      risks.push(`Small sample sizes for variants: ${smallSamples.map(r => r.variantId).join(', ')}`)
    }
    
    const highVariability = results.filter(r => r.standardError > 0.1)
    if (highVariability.length > 0) {
      risks.push(`High variability detected - results may be unstable`)
    }
    
    const marginalResults = results.filter(r => r.pValue > 0.01 && r.pValue < 0.05)
    if (marginalResults.length > 0) {
      risks.push(`Marginal significance - consider extending test duration`)
    }
    
    return risks
  }

  private generateNextSteps(results: StatisticalResult[], winner?: string): string[] {
    const steps: string[] = []
    
    if (winner) {
      steps.push(`Implement winning variant ${winner} to 100% of traffic`)
      steps.push(`Monitor post-launch metrics for 2 weeks`)
      steps.push(`Plan next iteration based on learnings`)
    } else {
      steps.push(`Continue running experiment until statistical significance`)
      steps.push(`Consider increasing traffic allocation if sample size is low`)
      steps.push(`Review experiment design and hypothesis`)
    }
    
    return steps
  }

  private determineExperimentStatus(results: StatisticalResult[]): 'running' | 'completed' | 'stopped' {
    const hasWinner = results.some(r => r.recommendedAction === 'ship')
    const hasKill = results.some(r => r.recommendedAction === 'kill')
    
    if (hasWinner || hasKill) return 'completed'
    
    const allExtended = results.every(r => r.recommendedAction === 'extend')
    if (allExtended) return 'stopped'
    
    return 'running'
  }
}