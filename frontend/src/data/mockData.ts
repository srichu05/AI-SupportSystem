import { ComplaintTicket, ComplaintAnalysis, PolicyDocument, TonePreset } from '../types';

export const MOCK_POLICIES: PolicyDocument[] = [
  {
    policy_id: 'POL-REFUND-2026',
    title: 'Enterprise Refund & Return Policy',
    version: 'v2.4',
    category: 'Billing & Returns',
    updated_at: '2026-09-15T00:00:00Z',
    total_chunks: 48,
    status: 'active',
  },
  {
    policy_id: 'POL-SHIPPING-2026',
    title: 'Shipping & Fulfillment SLA',
    version: 'v1.8',
    category: 'Logistics',
    updated_at: '2026-08-20T00:00:00Z',
    total_chunks: 24,
    status: 'active',
  },
  {
    policy_id: 'POL-WARRANTY-2026',
    title: 'Hardware Warranty & Defect Terms',
    version: 'v3.0',
    category: 'Technical Hardware',
    updated_at: '2026-07-01T00:00:00Z',
    total_chunks: 62,
    status: 'active',
  },
  {
    policy_id: 'POL-CONDUCT-2026',
    title: 'Logistics Partner Code of Conduct',
    version: 'v3.1',
    category: 'Operations',
    updated_at: '2026-06-12T00:00:00Z',
    total_chunks: 18,
    status: 'active',
  },
];

export const MOCK_TICKETS: ComplaintTicket[] = [
  {
    complaint_id: 'CMP-2026-9042',
    customer_id: 'CUST-8102',
    customer_name: 'Eleanor Vance',
    customer_email: 'eleanor.vance@example.com',
    channel: 'email',
    received_at: '2026-10-10 14:22:00',
    raw_text:
      'I received my order #48192 three days late, and when I opened the box, the espresso machine was dented and leaking water. Your delivery driver was dismissive and refused to note the damage on the receipt. I demand an immediate full refund and a $100 gift card for my trouble.',
    overall_sentiment: 'frustrated',
    overall_severity: 'high',
    review_status: 'PENDING_REVIEW',
  },
  {
    complaint_id: 'CMP-2026-9043',
    customer_id: 'CUST-5219',
    customer_name: 'Marcus Chen',
    customer_email: 'marcus.chen@example.com',
    channel: 'ticket',
    received_at: '2026-10-10 13:05:00',
    raw_text:
      'I was double billed for my Enterprise Cloud subscription renewal on October 1st. My card statement shows two identical charges of $249.99. Please refund the duplicate transaction immediately.',
    overall_sentiment: 'negative',
    overall_severity: 'medium',
    review_status: 'PENDING_REVIEW',
  },
  {
    complaint_id: 'CMP-2026-9044',
    customer_id: 'CUST-3941',
    customer_name: 'Sophia Al-Mansoor',
    customer_email: 'sophia.almansoor@example.com',
    channel: 'chat',
    received_at: '2026-10-10 11:40:00',
    raw_text:
      'My smart home thermostat purchased 16 months ago has started smoking from the rear capacitor. Your 12-month warranty is expired, but this is a hazardous defect. I expect a free replacement unit and compensation for electrician inspection costs.',
    overall_sentiment: 'urgent',
    overall_severity: 'critical',
    review_status: 'PENDING_REVIEW',
  },
];

export const MOCK_ANALYSES: Record<string, Record<TonePreset, ComplaintAnalysis>> = {
  'CMP-2026-9042': {
    empathetic: {
      complaint_id: 'CMP-2026-9042',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'frustrated',
      overall_severity: 'high',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Damaged Merchandise',
          summary: 'Espresso machine arrived dented with internal water leakage.',
          severity: 'high',
          status: 'covered',
          rationale: 'Active policy explicitly guarantees full replacement or refund upon photo proof within 14 days.',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-3',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 3.2 (Transit Damage)',
              section_name: 'Section 3: Damaged or Defective Items',
              page_number: 4,
              excerpt:
                'Goods damaged during transit are eligible for an immediate replacement or full refund upon submission of photographic evidence within 14 days of delivery receipt.',
              confidence_score: 0.95,
            },
          ],
        },
        {
          concern_id: 'CONC-2',
          category: 'Carrier Delay',
          summary: 'Shipment delivered 3 days past promised SLA delivery window.',
          severity: 'medium',
          status: 'partially_covered',
          rationale: 'Carrier delay past 48 hours qualifies for shipping fee credit, but not item value refund.',
          citations: [
            {
              citation_id: 'CIT-POL-02-SEC-2',
              document_title: 'Shipping & Fulfillment SLA v1.8',
              clause_id: 'Clause 2.1 (Standard Delay Recourse)',
              section_name: 'Section 2: Delivery Guarantees',
              page_number: 2,
              excerpt:
                'For carrier delays exceeding 48 hours beyond the guaranteed window, standard shipping charges shall be credited to the customer account.',
              confidence_score: 0.89,
            },
          ],
        },
        {
          concern_id: 'CONC-3',
          category: 'Courier Demeanor',
          summary: 'Delivery driver was dismissive and refused to record transit damage.',
          severity: 'low',
          status: 'needs_human_review',
          rationale: 'Courier behavioral reports require tier-1 agent submission to logistics vendor council.',
          citations: [
            {
              citation_id: 'CIT-POL-04-SEC-1',
              document_title: 'Logistics Partner Code of Conduct v3.1',
              clause_id: 'Clause 1.4 (Driver Escalation Protocol)',
              section_name: 'Section 1: Service Quality',
              page_number: 1,
              excerpt:
                'Courier behavioral complaints are logged to the 3PL Logistics Partner Council for formal review within 5 business days.',
              confidence_score: 0.81,
            },
          ],
        },
        {
          concern_id: 'CONC-4',
          category: 'Inconvenience Compensation',
          summary: 'Customer demanded an unprompted $100 gift card compensation.',
          severity: 'medium',
          status: 'prohibited',
          rationale: 'Company guidelines strictly cap frontline discretionary credits at $25. $100 gift card is prohibited.',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-7',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 7.1 (Discretionary Goodwill Limits)',
              section_name: 'Section 7: Consequential Goodwill & Credit',
              page_number: 9,
              excerpt:
                'Goodwill store credits exceeding $25 require written authorization from a Support Operations Director and may not be promised by frontline agents.',
              confidence_score: 0.97,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'FLAGGED',
        unsupported_commitments_detected: [
          {
            claim: 'Demand for $100 gift card compensation',
            reason: 'Exceeds authorized frontline discretionary credit threshold ($25 max). Prohibited by Clause 7.1.',
            severity: 'CRITICAL',
          },
        ],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'empathetic',
        subject: 'Regarding your order #48192 — Resolution & Next Steps',
        body: `Dear Eleanor,

Thank you for reaching out, and please accept our sincere apologies for the distress caused by the delay in your delivery, the damage to your espresso machine, and the unacceptable conduct of the courier.

Under our Enterprise Return Policy [Clause 3.2], we are prepared to immediately issue a replacement espresso machine or full refund as soon as you provide a photo of the exterior dent and leak. In addition, per our Shipping SLA [Clause 2.1], we have refunded the standard shipping fee to your original payment method due to the transit delay.

We take courier service standards seriously and have submitted a formal incident report to our logistics partner [Clause 1.4]. Regarding additional compensation, our policy limits discretionary goodwill credits to $25 and cannot accommodate third-party gift cards [Clause 7.1], but our immediate priority is ensuring you receive a flawless, fully functional machine without any extra cost.

Please reply with photos of the damaged unit so our team can expedite your replacement dispatch today.`,
        anchored_clause_ids: [
          'Clause 3.2 (Transit Damage)',
          'Clause 2.1 (Standard Delay Recourse)',
          'Clause 1.4 (Driver Escalation Protocol)',
          'Clause 7.1 (Discretionary Goodwill Limits)',
        ],
      },
      human_review_required: true,
      review_reasons: [
        'Transit damage verification required',
        'Unauthorized $100 goodwill claim flagged by guardrails',
        'Courier conduct report logged',
      ],
    },
    concise: {
      complaint_id: 'CMP-2026-9042',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'frustrated',
      overall_severity: 'high',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Damaged Merchandise',
          summary: 'Espresso machine dented with water leak.',
          severity: 'high',
          status: 'covered',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-3',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 3.2 (Transit Damage)',
              section_name: 'Section 3: Damaged or Defective Items',
              page_number: 4,
              excerpt:
                'Goods damaged during transit are eligible for an immediate replacement or full refund upon submission of photographic evidence within 14 days of delivery receipt.',
              confidence_score: 0.95,
            },
          ],
        },
        {
          concern_id: 'CONC-2',
          category: 'Carrier Delay',
          summary: 'Shipment delayed 3 days.',
          severity: 'medium',
          status: 'partially_covered',
          citations: [
            {
              citation_id: 'CIT-POL-02-SEC-2',
              document_title: 'Shipping & Fulfillment SLA v1.8',
              clause_id: 'Clause 2.1 (Standard Delay Recourse)',
              section_name: 'Section 2: Delivery Guarantees',
              page_number: 2,
              excerpt:
                'For carrier delays exceeding 48 hours beyond the guaranteed window, standard shipping charges shall be credited to the customer account.',
              confidence_score: 0.89,
            },
          ],
        },
        {
          concern_id: 'CONC-3',
          category: 'Courier Demeanor',
          summary: 'Driver refused to record transit damage.',
          severity: 'low',
          status: 'needs_human_review',
          citations: [
            {
              citation_id: 'CIT-POL-04-SEC-1',
              document_title: 'Logistics Partner Code of Conduct v3.1',
              clause_id: 'Clause 1.4 (Driver Escalation Protocol)',
              section_name: 'Section 1: Service Quality',
              page_number: 1,
              excerpt:
                'Courier behavioral complaints are logged to the 3PL Logistics Partner Council for formal review within 5 business days.',
              confidence_score: 0.81,
            },
          ],
        },
        {
          concern_id: 'CONC-4',
          category: 'Inconvenience Compensation',
          summary: '$100 gift card demanded.',
          severity: 'medium',
          status: 'prohibited',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-7',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 7.1 (Discretionary Goodwill Limits)',
              section_name: 'Section 7: Consequential Goodwill & Credit',
              page_number: 9,
              excerpt:
                'Goodwill store credits exceeding $25 require written authorization from a Support Operations Director and may not be promised by frontline agents.',
              confidence_score: 0.97,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'FLAGGED',
        unsupported_commitments_detected: [
          {
            claim: 'Demand for $100 gift card compensation',
            reason: 'Exceeds authorized frontline discretionary credit threshold ($25 max). Prohibited by Clause 7.1.',
            severity: 'CRITICAL',
          },
        ],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'concise',
        subject: 'Resolution: Order #48192 Damaged Delivery',
        body: `Hello Eleanor,

1. **Damaged Espresso Machine**: Per Clause 3.2, please reply with photos of the dent and leak so we can dispatch a replacement or issue a full refund immediately.
2. **Shipping Delay**: Per Clause 2.1, your standard shipping fee has been refunded due to the 3-day carrier delay.
3. **Driver Conduct**: A formal review was submitted to our logistics partner under Clause 1.4.
4. **Compensation Request**: Per Clause 7.1, discretionary credits are capped at $25 and external gift cards cannot be authorized.

Reply with your photos to trigger the replacement dispatch.`,
        anchored_clause_ids: [
          'Clause 3.2 (Transit Damage)',
          'Clause 2.1 (Standard Delay Recourse)',
          'Clause 1.4 (Driver Escalation Protocol)',
          'Clause 7.1 (Discretionary Goodwill Limits)',
        ],
      },
      human_review_required: true,
      review_reasons: [
        'Transit damage verification required',
        'Unauthorized $100 goodwill claim flagged by guardrails',
      ],
    },
    formal: {
      complaint_id: 'CMP-2026-9042',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'frustrated',
      overall_severity: 'high',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Damaged Merchandise',
          summary: 'Espresso machine arrived dented with internal water leakage.',
          severity: 'high',
          status: 'covered',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-3',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 3.2 (Transit Damage)',
              section_name: 'Section 3: Damaged or Defective Items',
              page_number: 4,
              excerpt:
                'Goods damaged during transit are eligible for an immediate replacement or full refund upon submission of photographic evidence within 14 days of delivery receipt.',
              confidence_score: 0.95,
            },
          ],
        },
        {
          concern_id: 'CONC-2',
          category: 'Carrier Delay',
          summary: 'Shipment delivered 3 days past SLA window.',
          severity: 'medium',
          status: 'partially_covered',
          citations: [
            {
              citation_id: 'CIT-POL-02-SEC-2',
              document_title: 'Shipping & Fulfillment SLA v1.8',
              clause_id: 'Clause 2.1 (Standard Delay Recourse)',
              section_name: 'Section 2: Delivery Guarantees',
              page_number: 2,
              excerpt:
                'For carrier delays exceeding 48 hours beyond the guaranteed window, standard shipping charges shall be credited to the customer account.',
              confidence_score: 0.89,
            },
          ],
        },
        {
          concern_id: 'CONC-3',
          category: 'Courier Demeanor',
          summary: 'Delivery driver conduct incident logged.',
          severity: 'low',
          status: 'needs_human_review',
          citations: [
            {
              citation_id: 'CIT-POL-04-SEC-1',
              document_title: 'Logistics Partner Code of Conduct v3.1',
              clause_id: 'Clause 1.4 (Driver Escalation Protocol)',
              section_name: 'Section 1: Service Quality',
              page_number: 1,
              excerpt:
                'Courier behavioral complaints are logged to the 3PL Logistics Partner Council for formal review within 5 business days.',
              confidence_score: 0.81,
            },
          ],
        },
        {
          concern_id: 'CONC-4',
          category: 'Inconvenience Compensation',
          summary: 'Customer demanded $100 gift card compensation.',
          severity: 'medium',
          status: 'prohibited',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-7',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 7.1 (Discretionary Goodwill Limits)',
              section_name: 'Section 7: Consequential Goodwill & Credit',
              page_number: 9,
              excerpt:
                'Goodwill store credits exceeding $25 require written authorization from a Support Operations Director and may not be promised by frontline agents.',
              confidence_score: 0.97,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'FLAGGED',
        unsupported_commitments_detected: [
          {
            claim: 'Demand for $100 gift card compensation',
            reason: 'Exceeds authorized frontline discretionary credit threshold ($25 max). Prohibited by Clause 7.1.',
            severity: 'CRITICAL',
          },
        ],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'formal',
        subject: 'Official Response: Ticket #48192 Transit Damage & Delivery Notice',
        body: `Dear Ms. Vance,

We write in formal acknowledgment of your correspondence concerning Order #48192.

In accordance with Section 3, Clause 3.2 of the Enterprise Return Policy, items sustaining damage during transit are eligible for comprehensive replacement or full refund upon receipt of photographic documentation verifying condition. Please provide these records to enable immediate processing.

Furthermore, pursuant to Clause 2.1 of our Fulfillment SLA, standard shipping costs have been credited to your account following the verified delivery delay. With respect to delivery personnel demeanor, a formal inquiry has been initiated under Logistics Code of Conduct Clause 1.4.

Please note that discretionary goodwill concessions are strictly governed by Clause 7.1 and cannot encompass third-party financial gift cards.

Respectfully,
Support Operations Compliance Group`,
        anchored_clause_ids: [
          'Clause 3.2 (Transit Damage)',
          'Clause 2.1 (Standard Delay Recourse)',
          'Clause 1.4 (Driver Escalation Protocol)',
          'Clause 7.1 (Discretionary Goodwill Limits)',
        ],
      },
      human_review_required: true,
      review_reasons: [
        'Transit damage verification required',
        'Unauthorized $100 goodwill claim flagged by guardrails',
      ],
    },
  },
  'CMP-2026-9043': {
    empathetic: {
      complaint_id: 'CMP-2026-9043',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'negative',
      overall_severity: 'medium',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Billing Discrepancy',
          summary: 'Duplicate credit card transaction of $249.99 for renewal.',
          severity: 'high',
          status: 'covered',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-2',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 2.4 (Erroneous Charges)',
              section_name: 'Section 2: Subscription Renewals & Billing',
              page_number: 3,
              excerpt:
                'Duplicate or unauthorized subscription transactions confirmed by payment processor records shall be credited back within 3-5 business days without service interruption.',
              confidence_score: 0.98,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'PASSED',
        unsupported_commitments_detected: [],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'empathetic',
        subject: 'Resolution: Duplicate Subscription Charge Refund',
        body: `Hi Marcus,

Thank you for bringing this to our attention. I apologize for the confusion and concern caused by the duplicate billing on your renewal.

I reviewed your account records and confirmed that two transactions of $249.99 were processed on October 1st. In accordance with Clause 2.4 of our Billing Policy, I have immediately initiated a full refund for the second transaction ($249.99) back to your card. This will reflect within 3-5 business days.

Your Enterprise Cloud service remains fully active with no disruption.`,
        anchored_clause_ids: ['Clause 2.4 (Erroneous Charges)'],
      },
      human_review_required: false,
      review_reasons: [],
    },
    concise: {
      complaint_id: 'CMP-2026-9043',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'negative',
      overall_severity: 'medium',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Billing Discrepancy',
          summary: 'Duplicate charge of $249.99 confirmed.',
          severity: 'high',
          status: 'covered',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-2',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 2.4 (Erroneous Charges)',
              section_name: 'Section 2: Subscription Renewals & Billing',
              page_number: 3,
              excerpt:
                'Duplicate or unauthorized subscription transactions confirmed by payment processor records shall be credited back within 3-5 business days without service interruption.',
              confidence_score: 0.98,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'PASSED',
        unsupported_commitments_detected: [],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'concise',
        subject: 'Refund Processed: Duplicate Charge ($249.99)',
        body: `Hello Marcus,

Per Clause 2.4, we verified the duplicate billing on October 1st and issued a refund of $249.99 to your original payment method. Expect funds within 3-5 business days. Your subscription remains active.`,
        anchored_clause_ids: ['Clause 2.4 (Erroneous Charges)'],
      },
      human_review_required: false,
      review_reasons: [],
    },
    formal: {
      complaint_id: 'CMP-2026-9043',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'negative',
      overall_severity: 'medium',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Billing Discrepancy',
          summary: 'Duplicate transaction verification and adjustment.',
          severity: 'high',
          status: 'covered',
          citations: [
            {
              citation_id: 'CIT-POL-01-SEC-2',
              document_title: 'Enterprise Refund & Return Policy v2.4',
              clause_id: 'Clause 2.4 (Erroneous Charges)',
              section_name: 'Section 2: Subscription Renewals & Billing',
              page_number: 3,
              excerpt:
                'Duplicate or unauthorized subscription transactions confirmed by payment processor records shall be credited back within 3-5 business days without service interruption.',
              confidence_score: 0.98,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'PASSED',
        unsupported_commitments_detected: [],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'formal',
        subject: 'Billing Adjustment Notice: Account Renewal Transaction',
        body: `Dear Mr. Chen,

Following verification of transaction logs for October 1st, an erroneous duplicate renewal debit was confirmed. 

Pursuant to Billing Policy Clause 2.4, a reimbursement in the amount of $249.99 has been authorized to the card on file. Settlement is anticipated within 3 to 5 business days. Your enterprise license terms remain fully operational.`,
        anchored_clause_ids: ['Clause 2.4 (Erroneous Charges)'],
      },
      human_review_required: false,
      review_reasons: [],
    },
  },
  'CMP-2026-9044': {
    empathetic: {
      complaint_id: 'CMP-2026-9044',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'urgent',
      overall_severity: 'critical',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Safety Hazard (Electrical Thermal Event)',
          summary: 'Thermostat rear capacitor smoking in home.',
          severity: 'critical',
          status: 'needs_human_review',
          rationale: 'Active smoke and thermal failure triggers immediate escalation to Safety Engineering & Legal.',
          citations: [
            {
              citation_id: 'CIT-POL-03-SEC-5',
              document_title: 'Hardware Warranty & Defect Terms v3.0',
              clause_id: 'Clause 5.1 (Thermal & Fire Safety Escalation)',
              section_name: 'Section 5: Hazard Triage',
              page_number: 8,
              excerpt:
                'Any reports of smoking components, scorched casings, or potential electrical fire hazards must be escalated immediately to Hardware Safety Engineering within 1 hour.',
              confidence_score: 0.99,
            },
          ],
        },
        {
          concern_id: 'CONC-2',
          category: 'Warranty Term Expiration',
          summary: 'Device is 16 months old (exceeds 12-month standard warranty).',
          severity: 'medium',
          status: 'prohibited',
          rationale: 'Standard limited warranty covers defects for 12 months from purchase date. Replacement prohibited by frontline agent.',
          citations: [
            {
              citation_id: 'CIT-POL-03-SEC-1',
              document_title: 'Hardware Warranty & Defect Terms v3.0',
              clause_id: 'Clause 1.2 (Coverage Period)',
              section_name: 'Section 1: Limited Warranty',
              page_number: 1,
              excerpt:
                'The standard hardware warranty terminates strictly 365 days post-retail activation. Discretionary post-warranty replacements are invalid without Product Director waiver.',
              confidence_score: 0.94,
            },
          ],
        },
        {
          concern_id: 'CONC-3',
          category: 'Electrician Consequential Costs',
          summary: 'Demand for compensation of private electrician inspection fees.',
          severity: 'high',
          status: 'prohibited',
          rationale: 'Policy excludes all incidental, indirect, or consequential home service fees.',
          citations: [
            {
              citation_id: 'CIT-POL-03-SEC-8',
              document_title: 'Hardware Warranty & Defect Terms v3.0',
              clause_id: 'Clause 8.4 (Exclusion of Consequential Damages)',
              section_name: 'Section 8: Liability Limitations',
              page_number: 14,
              excerpt:
                'The company disclaims liability for independent contractor, electrician, or installation fees incurred without prior written dispatch authorization.',
              confidence_score: 0.96,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'FLAGGED',
        unsupported_commitments_detected: [
          {
            claim: 'Demand for electrician compensation & out-of-warranty replacement',
            reason: 'Consequential damages disclaimed under Clause 8.4; 16-month device exceeds 12-month limit (Clause 1.2).',
            severity: 'CRITICAL',
          },
        ],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'empathetic',
        subject: 'URGENT: Thermostat Safety Notice & Case Escalation',
        body: `Dear Sophia,

Thank you for alerting us to this situation immediately. Your personal safety is our highest priority, and we urge you to keep the thermostat disconnected at the circuit breaker until inspected.

Under our Hardware Safety Protocol [Clause 5.1], I have escalated your case directly to our Hardware Safety Engineering team for immediate review. An engineering specialist will contact you directly within 24 hours.

Please note that standard warranty guidelines [Clause 1.2] and liability terms [Clause 8.4] address out-of-warranty replacements and third-party electrician fees, which require specialized review during product safety investigations. Our priority is ensuring the safety of your home setup.`,
        anchored_clause_ids: [
          'Clause 5.1 (Thermal & Fire Safety Escalation)',
          'Clause 1.2 (Coverage Period)',
          'Clause 8.4 (Exclusion of Consequential Damages)',
        ],
      },
      human_review_required: true,
      review_reasons: [
        'CRITICAL: Electrical thermal hazard reported',
        'Guardrail flagged prohibited out-of-warranty claims',
        'Product safety engineering escalation required',
      ],
    },
    concise: {
      complaint_id: 'CMP-2026-9044',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'urgent',
      overall_severity: 'critical',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Safety Hazard',
          summary: 'Thermostat smoking.',
          severity: 'critical',
          status: 'needs_human_review',
          citations: [
            {
              citation_id: 'CIT-POL-03-SEC-5',
              document_title: 'Hardware Warranty & Defect Terms v3.0',
              clause_id: 'Clause 5.1 (Thermal & Fire Safety Escalation)',
              section_name: 'Section 5: Hazard Triage',
              page_number: 8,
              excerpt:
                'Any reports of smoking components, scorched casings, or potential electrical fire hazards must be escalated immediately to Hardware Safety Engineering within 1 hour.',
              confidence_score: 0.99,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'FLAGGED',
        unsupported_commitments_detected: [
          {
            claim: 'Electrician costs & out-of-warranty unit',
            reason: 'Prohibited by Clauses 1.2 & 8.4.',
            severity: 'CRITICAL',
          },
        ],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'concise',
        subject: 'Safety Escalation: Thermostat Hardware Report',
        body: `Hello Sophia,

Please disconnect power to the thermostat immediately. Per Clause 5.1, your ticket is escalated to Hardware Safety Engineering. A safety lead will contact you within 24 hours. Out-of-warranty claims (Clause 1.2) and contractor fees (Clause 8.4) will be evaluated as part of this safety review.`,
        anchored_clause_ids: ['Clause 5.1 (Thermal & Fire Safety Escalation)'],
      },
      human_review_required: true,
      review_reasons: ['CRITICAL: Safety hazard reported'],
    },
    formal: {
      complaint_id: 'CMP-2026-9044',
      analysis_timestamp: new Date().toISOString(),
      overall_sentiment: 'urgent',
      overall_severity: 'critical',
      decomposed_concerns: [
        {
          concern_id: 'CONC-1',
          category: 'Hazard Triage',
          summary: 'Component thermal event.',
          severity: 'critical',
          status: 'needs_human_review',
          citations: [
            {
              citation_id: 'CIT-POL-03-SEC-5',
              document_title: 'Hardware Warranty & Defect Terms v3.0',
              clause_id: 'Clause 5.1 (Thermal & Fire Safety Escalation)',
              section_name: 'Section 5: Hazard Triage',
              page_number: 8,
              excerpt:
                'Any reports of smoking components, scorched casings, or potential electrical fire hazards must be escalated immediately to Hardware Safety Engineering within 1 hour.',
              confidence_score: 0.99,
            },
          ],
        },
      ],
      guardrail_report: {
        verdict: 'FLAGGED',
        unsupported_commitments_detected: [
          {
            claim: 'Consequential fee coverage',
            reason: 'Excluded under Clause 8.4.',
            severity: 'CRITICAL',
          },
        ],
        policy_conflicts_detected: [],
        policy_gaps_detected: [],
      },
      grounded_draft: {
        tone: 'formal',
        subject: 'Formal Notice: Safety Engineering Referral Case #3941',
        body: `Dear Ms. Al-Mansoor,

Your report of a thermal event regarding the smart thermostat has initiated our mandatory Critical Incident Protocol under Clause 5.1. 

Please cease operating the device immediately. Hardware Safety Engineering has assumed jurisdiction over this case file. While Clause 1.2 limits standard warranty remedies to 12 months and Clause 8.4 disclaims independent contractor fees, our product safety directors will evaluate technical findings directly.`,
        anchored_clause_ids: ['Clause 5.1 (Thermal & Fire Safety Escalation)'],
      },
      human_review_required: true,
      review_reasons: ['CRITICAL: Electrical thermal hazard reported'],
    },
  },
};
