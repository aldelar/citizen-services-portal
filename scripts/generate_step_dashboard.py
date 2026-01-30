#!/usr/bin/env python3
"""Generate step completion statistics dashboard with fake data.

This script generates realistic fake data for step completions across
LADBS, LADWP, and LASAN agencies, then creates visualizations.
"""

import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict

# Step type definitions with human-readable names and realistic duration estimates
STEP_TYPES = {
    # LADBS Steps (Permits & Inspections)
    "PRM": {
        "name": "Permit Application",
        "agency": "LADBS",
        "description": "Apply for and obtain official permits",
        "min_days": 5,
        "max_days": 45,
        "avg_attempts": 1.2,
    },
    "INS": {
        "name": "City Inspection",
        "agency": "LADBS",
        "description": "Schedule and pass city inspections",
        "min_days": 1,
        "max_days": 14,
        "avg_attempts": 1.5,  # Inspections often need retries
    },
    "TRD": {
        "name": "Trade Work",
        "agency": "LADBS",
        "description": "Hire professionals and complete physical work",
        "min_days": 1,
        "max_days": 30,
        "avg_attempts": 1.0,
    },
    "DOC": {
        "name": "Document Preparation",
        "agency": "All",
        "description": "Gather required documents and materials",
        "min_days": 0.5,
        "max_days": 7,
        "avg_attempts": 1.0,
    },
    "PAY": {
        "name": "Payment Processing",
        "agency": "LADBS/LADWP",
        "description": "Pay fees, deposits, or charges",
        "min_days": 0.1,
        "max_days": 3,
        "avg_attempts": 1.0,
    },
    
    # LADWP Steps (Utility & Solar)
    "APP": {
        "name": "Application Submission",
        "agency": "LADWP",
        "description": "Submit non-permit applications (rebates, interconnection)",
        "min_days": 1,
        "max_days": 10,
        "avg_attempts": 1.1,
    },
    "ENR": {
        "name": "Program Enrollment",
        "agency": "LADWP",
        "description": "Sign up for rate plans or programs",
        "min_days": 1,
        "max_days": 30,
        "avg_attempts": 1.0,
    },
    
    # LASAN Steps (Waste & Pickup)
    "PCK": {
        "name": "Pickup Scheduling",
        "agency": "LASAN",
        "description": "Schedule pickups and drop-offs",
        "min_days": 3,
        "max_days": 21,
        "avg_attempts": 1.0,
    },
}

# Detailed step subtypes for more granular tracking
DETAILED_STEPS = {
    # LADBS - Permits
    "PRM-Electrical": {"base": "PRM", "name": "Electrical Permit", "min_days": 10, "max_days": 45},
    "PRM-Mechanical": {"base": "PRM", "name": "Mechanical/HVAC Permit", "min_days": 7, "max_days": 30},
    "PRM-Building": {"base": "PRM", "name": "Building Permit", "min_days": 14, "max_days": 60},
    "PRM-Plumbing": {"base": "PRM", "name": "Plumbing Permit", "min_days": 7, "max_days": 28},
    
    # LADBS - Inspections
    "INS-RoughElectrical": {"base": "INS", "name": "Rough Electrical Inspection", "min_days": 2, "max_days": 10},
    "INS-FinalElectrical": {"base": "INS", "name": "Final Electrical Inspection", "min_days": 2, "max_days": 14},
    "INS-RoughMechanical": {"base": "INS", "name": "Rough Mechanical Inspection", "min_days": 2, "max_days": 10},
    "INS-FinalMechanical": {"base": "INS", "name": "Final Mechanical Inspection", "min_days": 2, "max_days": 14},
    "INS-Final": {"base": "INS", "name": "Final Sign-off Inspection", "min_days": 3, "max_days": 21},
    
    # LADBS - Trade
    "TRD-Electrician": {"base": "TRD", "name": "Hire & Complete Electrical Work", "min_days": 3, "max_days": 21},
    "TRD-HVAC": {"base": "TRD", "name": "Hire & Complete HVAC Work", "min_days": 5, "max_days": 30},
    "TRD-Plumber": {"base": "TRD", "name": "Hire & Complete Plumbing Work", "min_days": 2, "max_days": 14},
    
    # LADWP - Applications
    "APP-Interconnection": {"base": "APP", "name": "Solar Interconnection Application", "min_days": 14, "max_days": 60},
    "APP-Rebate": {"base": "APP", "name": "Rebate Application", "min_days": 3, "max_days": 21},
    "APP-ServiceUpgrade": {"base": "APP", "name": "Service Upgrade Request", "min_days": 7, "max_days": 45},
    
    # LADWP - Enrollments
    "ENR-TOU": {"base": "ENR", "name": "TOU Rate Plan Enrollment", "min_days": 7, "max_days": 30},
    "ENR-Solar": {"base": "ENR", "name": "Solar Program Enrollment", "min_days": 3, "max_days": 14},
    "ENR-EV": {"base": "ENR", "name": "EV Charging Program", "min_days": 2, "max_days": 10},
    
    # LASAN - Pickups
    "PCK-Bulky": {"base": "PCK", "name": "Bulky Item Pickup", "min_days": 5, "max_days": 21},
    "PCK-Ewaste": {"base": "PCK", "name": "E-Waste Collection", "min_days": 3, "max_days": 14},
    "PCK-Hazardous": {"base": "PCK", "name": "Hazardous Waste Drop-off", "min_days": 1, "max_days": 7},
    
    # Document & Payment
    "DOC-Plans": {"base": "DOC", "name": "Prepare Plans & Drawings", "min_days": 2, "max_days": 14},
    "DOC-Specs": {"base": "DOC", "name": "Gather Equipment Specs", "min_days": 0.5, "max_days": 3},
    "PAY-Permit": {"base": "PAY", "name": "Pay Permit Fees", "min_days": 0.1, "max_days": 1},
    "PAY-Deposit": {"base": "PAY", "name": "Pay Service Deposit", "min_days": 0.1, "max_days": 2},
}


def generate_fake_completions(num_records: int = 500) -> List[Dict]:
    """Generate fake step completion records with realistic data."""
    completions = []
    
    # Weight distribution - some steps are more common than others
    step_weights = {
        "PRM-Electrical": 50,
        "PRM-Mechanical": 30,
        "PRM-Building": 20,
        "PRM-Plumbing": 15,
        "INS-RoughElectrical": 45,
        "INS-FinalElectrical": 40,
        "INS-RoughMechanical": 25,
        "INS-FinalMechanical": 22,
        "INS-Final": 35,
        "TRD-Electrician": 40,
        "TRD-HVAC": 25,
        "TRD-Plumber": 15,
        "APP-Interconnection": 35,
        "APP-Rebate": 45,
        "APP-ServiceUpgrade": 20,
        "ENR-TOU": 30,
        "ENR-Solar": 25,
        "ENR-EV": 15,
        "PCK-Bulky": 60,
        "PCK-Ewaste": 25,
        "PCK-Hazardous": 15,
        "DOC-Plans": 50,
        "DOC-Specs": 40,
        "PAY-Permit": 45,
        "PAY-Deposit": 20,
    }
    
    step_types = list(step_weights.keys())
    weights = list(step_weights.values())
    
    base_date = datetime(2025, 6, 1)
    
    for i in range(num_records):
        step_type = random.choices(step_types, weights=weights, k=1)[0]
        step_info = DETAILED_STEPS[step_type]
        base_info = STEP_TYPES[step_info["base"]]
        
        # Generate realistic duration
        min_days = step_info["min_days"]
        max_days = step_info["max_days"]
        
        # Use a distribution that favors middle values with occasional outliers
        duration_days = random.triangular(min_days, max_days, (min_days + max_days) / 2)
        
        # Add some variability for retries
        base_attempts = base_info["avg_attempts"]
        if random.random() < 0.15:  # 15% chance of retry needed
            attempts = random.randint(2, 4)
            duration_days *= (1 + (attempts - 1) * 0.3)  # Each retry adds ~30% time
        else:
            attempts = 1
        
        # Random completion date within the past 8 months
        days_ago = random.randint(0, 240)
        completed_at = base_date + timedelta(days=240 - days_ago)
        started_at = completed_at - timedelta(days=duration_days)
        
        completions.append({
            "id": f"COMP-{i+1:05d}",
            "stepType": step_type,
            "stepName": step_info["name"],
            "baseType": step_info["base"],
            "baseTypeName": STEP_TYPES[step_info["base"]]["name"],
            "agency": base_info["agency"],
            "durationDays": round(duration_days, 2),
            "attempts": attempts,
            "chainStartedAt": started_at.isoformat(),
            "completedAt": completed_at.isoformat(),
        })
    
    return completions


def compute_statistics(completions: List[Dict]) -> Dict:
    """Compute statistics from completions data."""
    
    # Group by various dimensions
    by_step_type = defaultdict(list)
    by_base_type = defaultdict(list)
    by_agency = defaultdict(list)
    
    for comp in completions:
        by_step_type[comp["stepType"]].append(comp)
        by_base_type[comp["baseType"]].append(comp)
        by_agency[comp["agency"]].append(comp)
    
    def calc_stats(items):
        durations = [i["durationDays"] for i in items]
        attempts = [i["attempts"] for i in items]
        return {
            "count": len(items),
            "avgDuration": round(sum(durations) / len(durations), 2),
            "minDuration": round(min(durations), 2),
            "maxDuration": round(max(durations), 2),
            "medianDuration": round(sorted(durations)[len(durations) // 2], 2),
            "avgAttempts": round(sum(attempts) / len(attempts), 2),
            "successRate": round(sum(1 for a in attempts if a == 1) / len(attempts) * 100, 1),
        }
    
    # Detailed step stats
    step_stats = {}
    for step_type, items in by_step_type.items():
        step_info = DETAILED_STEPS[step_type]
        step_stats[step_type] = {
            "name": step_info["name"],
            "agency": STEP_TYPES[step_info["base"]]["agency"],
            **calc_stats(items),
        }
    
    # Base type stats
    base_stats = {}
    for base_type, items in by_base_type.items():
        base_stats[base_type] = {
            "name": STEP_TYPES[base_type]["name"],
            **calc_stats(items),
        }
    
    # Agency stats
    agency_stats = {}
    for agency, items in by_agency.items():
        agency_stats[agency] = calc_stats(items)
    
    return {
        "totalCompletions": len(completions),
        "byStepType": step_stats,
        "byBaseType": base_stats,
        "byAgency": agency_stats,
    }


def generate_html_dashboard(stats: Dict, completions: List[Dict]) -> str:
    """Generate an HTML dashboard with charts using Chart.js."""
    
    # Prepare data for charts
    step_types = sorted(stats["byStepType"].items(), key=lambda x: -x[1]["count"])
    base_types = sorted(stats["byBaseType"].items(), key=lambda x: -x[1]["count"])
    
    # Group steps by agency for agency breakdown
    ladbs_steps = [(k, v) for k, v in step_types if v["agency"] == "LADBS"]
    ladwp_steps = [(k, v) for k, v in step_types if v["agency"] == "LADWP"]
    lasan_steps = [(k, v) for k, v in step_types if v["agency"] == "LASAN"]
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Citizen Services Portal - Step Efficiency Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #888;
            font-size: 1.1rem;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }}
        .card.highlight {{
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 242, 254, 0.1) 100%);
            border-color: rgba(79, 172, 254, 0.3);
        }}
        .card h3 {{
            font-size: 0.9rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .card .value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #4facfe;
        }}
        .card .unit {{
            font-size: 1rem;
            color: #666;
            margin-left: 5px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .chart-container h2 {{
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #fff;
        }}
        .chart-wrapper {{
            position: relative;
            height: 300px;
        }}
        .agency-section {{
            margin-bottom: 30px;
        }}
        .agency-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .agency-badge {{
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85rem;
        }}
        .agency-badge.ladbs {{ background: #ef4444; }}
        .agency-badge.ladwp {{ background: #3b82f6; }}
        .agency-badge.lasan {{ background: #22c55e; }}
        .steps-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .steps-table th, .steps-table td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .steps-table th {{
            background: rgba(255, 255, 255, 0.05);
            font-weight: 600;
            color: #888;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 1px;
        }}
        .steps-table tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}
        .duration-bar {{
            height: 8px;
            background: rgba(79, 172, 254, 0.2);
            border-radius: 4px;
            overflow: hidden;
            min-width: 100px;
        }}
        .duration-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            border-radius: 4px;
        }}
        .success-rate {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .success-rate.high {{ background: rgba(34, 197, 94, 0.2); color: #22c55e; }}
        .success-rate.medium {{ background: rgba(234, 179, 8, 0.2); color: #eab308; }}
        .success-rate.low {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Step Efficiency Dashboard</h1>
        <p>Citizen Services Portal - Performance Analytics across LA City Agencies</p>
    </div>
    
    <div class="summary-cards">
        <div class="card highlight">
            <h3>Total Completions</h3>
            <div class="value">{stats["totalCompletions"]:,}</div>
        </div>
        <div class="card">
            <h3>Step Types Tracked</h3>
            <div class="value">{len(stats["byStepType"])}</div>
        </div>
        <div class="card">
            <h3>Avg Duration</h3>
            <div class="value">{sum(s["avgDuration"] * s["count"] for s in stats["byStepType"].values()) / stats["totalCompletions"]:.1f}<span class="unit">days</span></div>
        </div>
        <div class="card">
            <h3>First-Try Success</h3>
            <div class="value">{sum(1 for c in completions if c["attempts"] == 1) / len(completions) * 100:.0f}<span class="unit">%</span></div>
        </div>
    </div>
    
    <div class="charts-grid">
        <div class="chart-container">
            <h2>📈 Completions by Step Category</h2>
            <div class="chart-wrapper">
                <canvas id="baseTypeChart"></canvas>
            </div>
        </div>
        <div class="chart-container">
            <h2>⏱️ Average Duration by Category</h2>
            <div class="chart-wrapper">
                <canvas id="durationChart"></canvas>
            </div>
        </div>
        <div class="chart-container">
            <h2>🏛️ Completions by Agency</h2>
            <div class="chart-wrapper">
                <canvas id="agencyChart"></canvas>
            </div>
        </div>
        <div class="chart-container">
            <h2>✅ First-Try Success Rate by Category</h2>
            <div class="chart-wrapper">
                <canvas id="successChart"></canvas>
            </div>
        </div>
    </div>
    
    <!-- LADBS Section -->
    <div class="agency-section card">
        <div class="agency-header">
            <span class="agency-badge ladbs">LADBS</span>
            <h2>LA Department of Building & Safety</h2>
        </div>
        <table class="steps-table">
            <thead>
                <tr>
                    <th>Step Type</th>
                    <th>Count</th>
                    <th>Avg Duration</th>
                    <th>Duration Range</th>
                    <th>Success Rate</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f'''
                <tr>
                    <td><strong>{v["name"]}</strong></td>
                    <td>{v["count"]}</td>
                    <td>{v["avgDuration"]:.1f} days</td>
                    <td>
                        <div class="duration-bar">
                            <div class="duration-bar-fill" style="width: {min(v["avgDuration"] / 60 * 100, 100)}%"></div>
                        </div>
                        <small style="color: #666">{v["minDuration"]:.1f} - {v["maxDuration"]:.1f} days</small>
                    </td>
                    <td><span class="success-rate {'high' if v['successRate'] >= 85 else 'medium' if v['successRate'] >= 70 else 'low'}">{v["successRate"]:.0f}%</span></td>
                </tr>''' for k, v in ladbs_steps)}
            </tbody>
        </table>
    </div>
    
    <!-- LADWP Section -->
    <div class="agency-section card">
        <div class="agency-header">
            <span class="agency-badge ladwp">LADWP</span>
            <h2>LA Department of Water & Power</h2>
        </div>
        <table class="steps-table">
            <thead>
                <tr>
                    <th>Step Type</th>
                    <th>Count</th>
                    <th>Avg Duration</th>
                    <th>Duration Range</th>
                    <th>Success Rate</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f'''
                <tr>
                    <td><strong>{v["name"]}</strong></td>
                    <td>{v["count"]}</td>
                    <td>{v["avgDuration"]:.1f} days</td>
                    <td>
                        <div class="duration-bar">
                            <div class="duration-bar-fill" style="width: {min(v["avgDuration"] / 60 * 100, 100)}%"></div>
                        </div>
                        <small style="color: #666">{v["minDuration"]:.1f} - {v["maxDuration"]:.1f} days</small>
                    </td>
                    <td><span class="success-rate {'high' if v['successRate'] >= 85 else 'medium' if v['successRate'] >= 70 else 'low'}">{v["successRate"]:.0f}%</span></td>
                </tr>''' for k, v in ladwp_steps)}
            </tbody>
        </table>
    </div>
    
    <!-- LASAN Section -->
    <div class="agency-section card">
        <div class="agency-header">
            <span class="agency-badge lasan">LASAN</span>
            <h2>LA Sanitation & Environment</h2>
        </div>
        <table class="steps-table">
            <thead>
                <tr>
                    <th>Step Type</th>
                    <th>Count</th>
                    <th>Avg Duration</th>
                    <th>Duration Range</th>
                    <th>Success Rate</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f'''
                <tr>
                    <td><strong>{v["name"]}</strong></td>
                    <td>{v["count"]}</td>
                    <td>{v["avgDuration"]:.1f} days</td>
                    <td>
                        <div class="duration-bar">
                            <div class="duration-bar-fill" style="width: {min(v["avgDuration"] / 60 * 100, 100)}%"></div>
                        </div>
                        <small style="color: #666">{v["minDuration"]:.1f} - {v["maxDuration"]:.1f} days</small>
                    </td>
                    <td><span class="success-rate {'high' if v['successRate'] >= 85 else 'medium' if v['successRate'] >= 70 else 'low'}">{v["successRate"]:.0f}%</span></td>
                </tr>''' for k, v in lasan_steps)}
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")} • Data represents simulated step completions for demonstration purposes</p>
    </div>
    
    <script>
        // Chart.js configuration
        Chart.defaults.color = '#888';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        
        const baseTypeData = {json.dumps({STEP_TYPES[k]["name"]: v["count"] for k, v in base_types})};
        const durationData = {json.dumps({STEP_TYPES[k]["name"]: v["avgDuration"] for k, v in base_types})};
        const agencyData = {json.dumps(stats["byAgency"])};
        const successData = {json.dumps({STEP_TYPES[k]["name"]: v["successRate"] for k, v in base_types})};
        
        // Base Type Chart
        new Chart(document.getElementById('baseTypeChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(baseTypeData),
                datasets: [{{
                    label: 'Completions',
                    data: Object.values(baseTypeData),
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.7)',
                        'rgba(249, 115, 22, 0.7)',
                        'rgba(234, 179, 8, 0.7)',
                        'rgba(34, 197, 94, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(139, 92, 246, 0.7)',
                        'rgba(236, 72, 153, 0.7)',
                        'rgba(156, 163, 175, 0.7)'
                    ],
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
        
        // Duration Chart
        new Chart(document.getElementById('durationChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(durationData),
                datasets: [{{
                    label: 'Avg Days',
                    data: Object.values(durationData),
                    backgroundColor: 'rgba(79, 172, 254, 0.7)',
                    borderRadius: 8
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{ beginAtZero: true, title: {{ display: true, text: 'Days' }} }}
                }}
            }}
        }});
        
        // Agency Chart
        new Chart(document.getElementById('agencyChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['LADBS', 'LADWP', 'LASAN', 'All Agencies'],
                datasets: [{{
                    data: [
                        agencyData['LADBS']?.count || 0,
                        agencyData['LADWP']?.count || 0,
                        agencyData['LASAN']?.count || 0,
                        (agencyData['All']?.count || 0) + (agencyData['LADBS/LADWP']?.count || 0)
                    ],
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(156, 163, 175, 0.8)'
                    ],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right'
                    }}
                }}
            }}
        }});
        
        // Success Rate Chart
        new Chart(document.getElementById('successChart'), {{
            type: 'bar',
            data: {{
                labels: Object.keys(successData),
                datasets: [{{
                    label: 'First-Try Success %',
                    data: Object.values(successData),
                    backgroundColor: Object.values(successData).map(v => 
                        v >= 85 ? 'rgba(34, 197, 94, 0.7)' : 
                        v >= 70 ? 'rgba(234, 179, 8, 0.7)' : 
                        'rgba(239, 68, 68, 0.7)'
                    ),
                    borderRadius: 8
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: '% Success' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
'''
    return html


def main():
    """Generate fake data and create dashboard."""
    print("🎲 Generating fake step completion data...")
    completions = generate_fake_completions(500)
    
    print("📊 Computing statistics...")
    stats = compute_statistics(completions)
    
    print("\n" + "=" * 60)
    print("📈 STEP COMPLETION STATISTICS SUMMARY")
    print("=" * 60)
    
    print(f"\n🔢 Total Completions: {stats['totalCompletions']}")
    
    print("\n📋 By Step Category:")
    for base_type, data in sorted(stats["byBaseType"].items(), key=lambda x: -x[1]["count"]):
        print(f"   {STEP_TYPES[base_type]['name']:25} | Count: {data['count']:4} | Avg: {data['avgDuration']:6.1f} days | Success: {data['successRate']:.0f}%")
    
    print("\n🏛️ By Agency:")
    for agency, data in stats["byAgency"].items():
        print(f"   {agency:15} | Count: {data['count']:4} | Avg: {data['avgDuration']:6.1f} days")
    
    print("\n🖼️ Generating HTML dashboard...")
    html = generate_html_dashboard(stats, completions)
    
    # Save HTML dashboard
    output_path = "/home/aldelar/Code/citizen-services-portal/scripts/step_efficiency_dashboard.html"
    with open(output_path, "w") as f:
        f.write(html)
    
    print(f"✅ Dashboard saved to: {output_path}")
    print("\n💡 Open the HTML file in a browser to view the interactive dashboard!")
    
    # Also save raw data as JSON for further analysis
    json_path = "/home/aldelar/Code/citizen-services-portal/scripts/step_stats_data.json"
    with open(json_path, "w") as f:
        json.dump({
            "statistics": stats,
            "completions": completions[:50],  # Sample of completions
            "stepTypes": DETAILED_STEPS,
            "baseTypes": STEP_TYPES,
        }, f, indent=2, default=str)
    
    print(f"📁 Raw data saved to: {json_path}")


if __name__ == "__main__":
    main()
