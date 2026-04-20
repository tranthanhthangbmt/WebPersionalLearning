const fs = require('fs');
const path = require('path');

const filesToFix = [
    'MD2-120 câu_updated.csv',
    'MD5-120 câu_updated.csv'
];
const targetLines = 121; // Header + 120 questions

filesToFix.forEach(fileName => {
    const filePath = path.join(__dirname, fileName);

    try {
        if (!fs.existsSync(filePath)) {
            console.log(`${fileName}: Not Found`);
            return;
        }

        const content = fs.readFileSync(filePath, 'utf8');
        // Split by newline, handling both \r\n and \n
        const lines = content.split(/\r?\n/);

        // Filter out empty lines at the end if any, to get accurate count
        const nonEmptyLines = lines.filter(line => line.trim() !== '');

        console.log(`${fileName} Original Lines: ${lines.length} (Non-empty: ${nonEmptyLines.length})`);

        if (lines.length > targetLines) {
            // Truncate
            const newLines = lines.slice(0, targetLines);
            const newContent = newLines.join('\n');

            fs.writeFileSync(filePath, newContent, 'utf8');
            console.log(`${fileName} Truncated to: ${newLines.length}`);
        } else {
            console.log(`${fileName} No change needed.`);
        }

    } catch (err) {
        console.error(`Error processing ${fileName}:`, err);
    }
});
