import { BaseEntity } from '@/types/common/base';
import { PaymentStatus, PaymentDetectionMethod, BillingDestination } from './documents';

// Billing router types preserving 4-destination system
export interface BillingRoute extends BaseEntity {
  document_id: string;
  tenant_id: string;

  // 4 billing destinations
  destination: BillingDestination;
  routing_confidence: number;
  routing_algorithm: RoutingAlgorithm;
  routing_factors: RoutingFactor[];

  // Enhanced routing logic
  rule_matches: RuleMatch[];
  override_reason?: string;
  manual_override: boolean;
  override_user_id?: string;

  // Audit and tracking
  routing_history: RoutingHistory[];
  validation_status: ValidationStatus;
  quality_score: number;
}

export type RoutingAlgorithm =
  | 'rule_based'
  | 'ml_classification'
  | 'hybrid'
  | 'manual_override';

export interface RoutingFactor {
  factor_type: 'payment_status' | 'vendor_type' | 'amount_threshold' | 'document_type' | 'gl_account';
  factor_value: string;
  weight: number;
  confidence: number;
}

export interface RuleMatch {
  rule_id: string;
  rule_name: string;
  match_score: number;
  conditions_met: string[];
  suggested_destination: BillingDestination;
}

export interface RoutingHistory {
  timestamp: string;
  previous_destination?: BillingDestination;
  new_destination: BillingDestination;
  reason: string;
  user_id?: string;
  confidence: number;
}

export type ValidationStatus = 'pending' | 'validated' | 'rejected' | 'under_review';

// Payment status detection preserving 5-method consensus
export interface PaymentDetection extends BaseEntity {
  document_id: string;
  tenant_id: string;

  // Final consensus result
  final_status: PaymentStatus;
  consensus_confidence: number;
  method_agreement_score: number;

  // 5 detection methods
  method_results: PaymentMethodResult[];
  consensus_algorithm: ConsensusAlgorithm;

  // Detection details
  payment_indicators: PaymentIndicator[];
  conflicting_signals: ConflictingSignal[];
  manual_verification: boolean;
  verification_notes?: string;
}

export interface PaymentMethodResult {
  method: PaymentDetectionMethod;
  status: PaymentStatus;
  confidence: number;
  processing_time_ms: number;
  evidence: Evidence[];
  error?: string;
}

export type ConsensusAlgorithm =
  | 'majority_vote'
  | 'weighted_confidence'
  | 'claude_prioritized'
  | 'manual_review_required';

export interface Evidence {
  type: 'text_pattern' | 'amount_match' | 'date_correlation' | 'visual_indicator' | 'metadata';
  description: string;
  confidence: number;
  location?: DocumentLocation;
  value?: string;
}

export interface DocumentLocation {
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PaymentIndicator {
  indicator_type: 'stamp' | 'watermark' | 'text_overlay' | 'amount_modification' | 'date_stamp';
  description: string;
  confidence: number;
  supporting_methods: PaymentDetectionMethod[];
}

export interface ConflictingSignal {
  methods_in_conflict: PaymentDetectionMethod[];
  conflict_description: string;
  resolution_strategy: string;
  human_review_needed: boolean;
}

// Billing destinations and management
export interface BillingDestinationConfig {
  destination: BillingDestination;
  tenant_id: string;

  // Configuration
  is_active: boolean;
  routing_rules: DestinationRule[];
  approval_workflow?: ApprovalWorkflow;
  notification_settings: NotificationSettings;

  // Statistics and monitoring
  document_count: number;
  total_amount: number;
  average_processing_time: number;
  accuracy_rate: number;
  last_used: string;
}

export interface DestinationRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  is_active: boolean;

  // Rule conditions
  conditions: RuleCondition[];
  logical_operator: 'AND' | 'OR';

  // Actions
  actions: RuleAction[];
  confidence_threshold: number;
}

export interface RuleCondition {
  field: 'payment_status' | 'vendor_name' | 'gl_account' | 'amount' | 'document_type';
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'in_list' | 'matches_pattern';
  value: any;
  weight: number;
}

export interface RuleAction {
  action_type: 'route_to_destination' | 'require_approval' | 'flag_for_review' | 'notify_user';
  parameters: Record<string, any>;
}

export interface ApprovalWorkflow {
  required_approvers: string[];
  approval_threshold: number;
  escalation_rules: EscalationRule[];
  timeout_minutes: number;
  auto_approve_conditions?: RuleCondition[];
}

export interface EscalationRule {
  trigger_condition: string;
  escalate_to: string[];
  timeout_minutes: number;
}

export interface NotificationSettings {
  email_notifications: boolean;
  slack_notifications?: boolean;
  webhook_url?: string;
  notification_events: NotificationEvent[];
}

export type NotificationEvent =
  | 'document_routed'
  | 'approval_required'
  | 'routing_failed'
  | 'manual_review_needed'
  | 'high_value_document';

// Payment analysis and insights
export interface PaymentAnalytics {
  tenant_id: string;
  period: {
    start_date: string;
    end_date: string;
  };

  // Method performance
  method_performance: MethodPerformance[];
  consensus_accuracy: number;
  manual_review_rate: number;

  // Payment patterns
  payment_status_distribution: PaymentStatusDistribution[];
  vendor_payment_patterns: VendorPaymentPattern[];
  seasonal_trends: PaymentSeasonalTrend[];

  // Quality metrics
  detection_quality_score: number;
  false_positive_rate: number;
  false_negative_rate: number;
  improvement_recommendations: string[];
}

export interface MethodPerformance {
  method: PaymentDetectionMethod;
  accuracy: number;
  precision: number;
  recall: number;
  average_confidence: number;
  processing_time_ms: number;
  reliability_score: number;
}

export interface PaymentStatusDistribution {
  status: PaymentStatus;
  count: number;
  percentage: number;
  total_amount: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface VendorPaymentPattern {
  vendor_name: string;
  payment_behavior: 'consistent' | 'irregular' | 'seasonal';
  average_payment_delay: number;
  payment_methods_used: string[];
  reliability_score: number;
}

export interface PaymentSeasonalTrend {
  period: 'Q1' | 'Q2' | 'Q3' | 'Q4' | string;
  payment_volume: number;
  average_amount: number;
  dominant_status: PaymentStatus;
  variance_from_average: number;
}

// Billing route optimization
export interface RouteOptimization {
  tenant_id: string;
  optimization_type: 'accuracy' | 'speed' | 'cost' | 'balanced';

  // Current performance
  current_metrics: RoutePerformanceMetrics;

  // Optimization suggestions
  suggested_rules: SuggestedRule[];
  threshold_adjustments: ThresholdAdjustment[];
  training_recommendations: TrainingRecommendation[];

  // Expected improvements
  expected_accuracy_gain: number;
  expected_speed_improvement: number;
  implementation_effort: 'low' | 'medium' | 'high';
}

export interface RoutePerformanceMetrics {
  accuracy: number;
  average_processing_time: number;
  manual_review_rate: number;
  error_rate: number;
  user_satisfaction_score: number;
}

export interface SuggestedRule {
  rule_name: string;
  description: string;
  conditions: RuleCondition[];
  expected_accuracy_improvement: number;
  affected_document_percentage: number;
  implementation_priority: 'high' | 'medium' | 'low';
}

export interface ThresholdAdjustment {
  parameter: string;
  current_value: number;
  suggested_value: number;
  justification: string;
  expected_impact: string;
}

export interface TrainingRecommendation {
  recommendation_type: 'more_training_data' | 'feature_engineering' | 'algorithm_update';
  description: string;
  estimated_effort_hours: number;
  expected_benefit: string;
  priority: number;
}