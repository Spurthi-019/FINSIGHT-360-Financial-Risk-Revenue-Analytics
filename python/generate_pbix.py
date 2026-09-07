import zipfile
import os

pbix_path = "FINSIGHT_360_Financial_Risk_Analytics.pbix"
with zipfile.ZipFile(pbix_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("Version", "1.28\n")
    zf.writestr("Settings", '{"Version": 1, "Type": "Report", "ModelType": "PBIDesktop"}')
    zf.writestr("Report/Layout", '{"id": 0, "resourcePackages": [], "sections": [{"displayName": "Executive Performance Overview", "name": "Section1"}, {"displayName": "Payment Performance & Gateway Reliability", "name": "Section2"}, {"displayName": "Fraud & Risk Analytics", "name": "Section3"}, {"displayName": "Customer Intelligence & Segment Dynamics", "name": "Section4"}, {"displayName": "Revenue Risk & Pareto Concentration", "name": "Section5"}, {"displayName": "Executive Recommendations & Strategic Roadmap", "name": "Section6"}]}')
    zf.writestr("DiagramLayout", '{"version": "1.0.0", "diagrams": []}')

print(f"Created {pbix_path} - Size: {os.path.getsize(pbix_path)} bytes")
