const fs = require('fs');
const path = 'MD3-120 câu_updated.csv';
const outFile = 'node_analysis.txt';

try {
    const data = fs.readFileSync(path, 'utf8');
    const lines = data.split(/\r?\n/);

    let output = `Total lines: ${lines.length}\n`;
    output += `File size: ${data.length}\n`;

    let emptyLines = 0;
    let commaOnlyLines = 0;
    let validLines = 0;

    lines.forEach((line, index) => {
        if (!line.trim()) {
            emptyLines++;
        } else if (line.replace(/,/g, '').trim() === '') {
            commaOnlyLines++;
        } else {
            validLines++;
        }

        if (index < 5) {
            output += `Line ${index}: ${JSON.stringify(line)}\n`;
        }
    });

    output += `Empty lines: ${emptyLines}\n`;
    output += `Comma-only lines: ${commaOnlyLines}\n`;
    output += `Valid lines: ${validLines}\n`;

    fs.writeFileSync(outFile, output);
    console.log("Analysis done");
} catch (e) {
    fs.writeFileSync(outFile, `Error: ${e.message}`);
}
