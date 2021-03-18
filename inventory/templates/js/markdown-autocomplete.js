const theTextarea = document.getElementById('{{ textarea }}');
const $theTextarea = $(theTextarea);
const ulRegex = /^- .+/;
const olRegex = /^\d+\. .+/;
const olNumberRegex = /^\d+/;
const emptyLiRegex = /^(-|(\d+\.)) $/;
const emptyOlLiRegex = /^\d+\. $/;

$theTextarea.on('keyup', e => {
    // `13` is the return key.
    if (e.which === 13) {
        const cursorPosition = $theTextarea.prop('selectionStart');
        const everything = $theTextarea.val();
        const beforeCursor = everything.slice(0, cursorPosition);
        const afterCursor = everything.slice(cursorPosition);
        let lines = beforeCursor.split('\n');
        const lastLine = lines[lines.length - 2];

        if (lastLine.match(ulRegex)) {
            $theTextarea.val(beforeCursor + '- ' + afterCursor);
            theTextarea.setSelectionRange(cursorPosition + 2, cursorPosition + 2);
        }

        if (lastLine.match(olRegex)) {
            let nextNumber = Number(olNumberRegex.exec(lastLine)[0]) + 1;
            let numberLength = nextNumber.toString().length + 2;
            $theTextarea.val(beforeCursor + `${nextNumber}. ` + afterCursor);
            theTextarea.setSelectionRange(cursorPosition + numberLength, cursorPosition + numberLength);
        }

        if (lastLine.match(emptyLiRegex)) {
            let offset = 3;

            if (lastLine.match(emptyOlLiRegex)) {
                offset += Number(olNumberRegex.exec(lastLine)[0].length);
            }

            lines.splice(-2, 1);
            $theTextarea.val(lines.join('\n') + '' + afterCursor);
            theTextarea.setSelectionRange(cursorPosition - offset, cursorPosition - offset);
        }
    }
});
