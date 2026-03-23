with open(r'C:\Users\harun\TradingAgents\cli\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

fixed = content.replace('with open(log_file, "a") as f:', 'with open(log_file, "a", encoding="utf-8") as f:')
fixed = fixed.replace('with open(report_dir / file_name, "w") as f:', 'with open(report_dir / file_name, "w", encoding="utf-8") as f:')

with open(r'C:\Users\harun\TradingAgents\cli\main.py', 'w', encoding='utf-8') as f:
    f.write(fixed)

print('Tamam!')
