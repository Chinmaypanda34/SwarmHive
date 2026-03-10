# report_generator.py
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel

router = APIRouter()

class ReportRequest(BaseModel):
    test_results: dict
    target_url: str
    template_used: str
    report_format: str = "html"  # html, json, pdf

@router.post("/generate-report")
async def generate_security_report(request: ReportRequest):
    """Generate comprehensive security assessment report"""
    try:
        # Create report data
        report_data = create_report_data(request)
        
        if request.report_format == "html":
            return generate_html_report(report_data)
        elif request.report_format == "json":
            return report_data
        else:
            return generate_html_report(report_data)  # Default to HTML
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

def create_report_data(request: ReportRequest):
    """Create structured report data from test results"""
    findings = request.test_results.get('findings', [])
    
    # Calculate statistics
    critical_count = len([f for f in findings if f.get('severity', '').lower() == 'high'])
    medium_count = len([f for f in findings if f.get('severity', '').lower() == 'medium'])
    low_count = len([f for f in findings if f.get('severity', '').lower() == 'low'])
    
    return {
        "metadata": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tool": "SwarmHive Security Scanner",
            "version": "2.0",
            "target": request.target_url,
            "template_used": request.template_used
        },
        "executive_summary": {
            "total_findings": len(findings),
            "critical_vulnerabilities": critical_count,
            "medium_vulnerabilities": medium_count,
            "low_vulnerabilities": low_count,
            "overall_risk": calculate_overall_risk(critical_count, medium_count),
            "security_score": calculate_security_score(findings)
        },
        "vulnerability_analysis": {
            "findings": findings,
            "test_steps": request.test_results.get('steps', [])
        },
        "recommendations": generate_recommendations(findings),
        "technical_details": {
            "test_evidence": extract_evidence(findings),
            "timeline": request.test_results.get('timeline', [])
        }
    }

def calculate_overall_risk(critical_count, medium_count):
    """Calculate overall risk level"""
    if critical_count > 0:
        return "HIGH"
    elif medium_count > 0:
        return "MEDIUM"
    else:
        return "LOW"

def calculate_security_score(findings):
    """Calculate security score (0-100)"""
    if not findings:
        return 100
    
    # Deduct points based on findings
    score = 100
    for finding in findings:
        severity = finding.get('severity', '').lower()
        if severity == 'high':
            score -= 30
        elif severity == 'medium':
            score -= 15
        elif severity == 'low':
            score -= 5
    
    return max(0, score)

def generate_recommendations(findings):
    """Generate remediation recommendations"""
    recommendations = []
    
    for finding in findings:
        vuln_type = finding.get('type', '').lower()
        
        if 'bola' in vuln_type:
            recommendations.append({
                "vulnerability": "BOLA (Broken Object Level Authorization)",
                "severity": "HIGH",
                "recommendation": "Implement proper authorization checks verifying user ownership before allowing resource access",
                "implementation": "Add user context validation in all object-level operations"
            })
        elif 'idor' in vuln_type:
            recommendations.append({
                "vulnerability": "IDOR (Insecure Direct Object Reference)",
                "severity": "HIGH", 
                "recommendation": "Use indirect reference maps instead of direct object references",
                "implementation": "Implement UUID-based references with user context validation"
            })
        elif 'jwt' in vuln_type:
            recommendations.append({
                "vulnerability": "JWT Token Issues",
                "severity": "MEDIUM",
                "recommendation": "Implement proper token validation and expiration",
                "implementation": "Add token scope validation and proper signature verification"
            })
    
    # Add general recommendations
    if not recommendations:
        recommendations.append({
            "vulnerability": "General Security",
            "severity": "INFO",
            "recommendation": "Continue regular security testing and monitoring",
            "implementation": "Schedule periodic security scans and implement API security monitoring"
        })
    
    return recommendations

def extract_evidence(findings):
    """Extract evidence from findings"""
    evidence = []
    for finding in findings:
        if finding.get('evidence'):
            evidence.append({
                "type": finding.get('type'),
                "evidence": finding.get('evidence'),
                "severity": finding.get('severity')
            })
    return evidence

def generate_html_report(report_data):
    """Generate HTML report"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SwarmHive Security Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 30px; border-radius: 10px; }}
            .summary {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .finding {{ border-left: 4px solid #e53e3e; padding: 15px; margin: 10px 0; background: #fff5f5; }}
            .finding.medium {{ border-left-color: #ed8936; background: #fef5e7; }}
            .finding.low {{ border-left-color: #38a169; background: #f0fff4; }}
            .recommendation {{ background: #ebf8ff; padding: 15px; margin: 10px 0; border-radius: 6px; }}
            .risk-high {{ color: #e53e3e; font-weight: bold; }}
            .risk-medium {{ color: #ed8936; font-weight: bold; }}
            .risk-low {{ color: #38a169; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ SwarmHive Security Assessment Report</h1>
            <p>Generated on: {report_data['metadata']['generated_at']}</p>
            <p>Target: {report_data['metadata']['target']}</p>
        </div>
        
        <div class="summary">
            <h2>📊 Executive Summary</h2>
            <p><strong>Security Score:</strong> {report_data['executive_summary']['security_score']}/100</p>
            <p><strong>Overall Risk:</strong> <span class="risk-{report_data['executive_summary']['overall_risk'].lower()}">{report_data['executive_summary']['overall_risk']}</span></p>
            <p><strong>Total Findings:</strong> {report_data['executive_summary']['total_findings']}</p>
            <p><strong>Critical Vulnerabilities:</strong> {report_data['executive_summary']['critical_vulnerabilities']}</p>
        </div>
        
        <h2>🔍 Vulnerability Findings</h2>
        {generate_findings_html(report_data['vulnerability_analysis']['findings'])}
        
        <h2>💡 Recommendations</h2>
        {generate_recommendations_html(report_data['recommendations'])}
        
        <div style="margin-top: 40px; padding: 20px; background: #f7fafc; border-radius: 8px;">
            <p><strong>Report Generated by:</strong> SwarmHive API Security Scanner v{report_data['metadata']['version']}</p>
            <p><em>This report is for security assessment purposes only.</em></p>
        </div>
    </body>
    </html>
    """
    
    return {"html_content": html_content, "report_data": report_data}

def generate_findings_html(findings):
    if not findings:
        return "<p>✅ No vulnerabilities found during this security assessment.</p>"
    
    findings_html = ""
    for finding in findings:
        severity_class = finding.get('severity', 'low').lower()
        findings_html += f"""
        <div class="finding {severity_class}">
            <h3>{finding.get('type', 'Unknown')} - <span class="risk-{severity_class}">{severity_class.upper()}</span></h3>
            <p><strong>Description:</strong> {finding.get('description', 'No description available')}</p>
            {f"<p><strong>Evidence:</strong> {json.dumps(finding.get('evidence', {}), indent=2)}</p>" if finding.get('evidence') else ""}
        </div>
        """
    return findings_html

def generate_recommendations_html(recommendations):
    if not recommendations:
        return "<p>No specific recommendations available.</p>"
    
    rec_html = ""
    for rec in recommendations:
        rec_html += f"""
        <div class="recommendation">
            <h3>{rec['vulnerability']} - <span class="risk-{rec['severity'].lower()}">{rec['severity']}</span></h3>
            <p><strong>Recommendation:</strong> {rec['recommendation']}</p>
            <p><strong>Implementation:</strong> {rec['implementation']}</p>
        </div>
        """
    return rec_html