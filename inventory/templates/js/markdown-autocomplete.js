const $textarea = $('textarea');
const ulRegex = /^- .+/;
const olRegex = /^\d+\. .+/;
const olNumberRegex = /^\d+/;
const emptyLiRegex = /^(-|(\d+\.)) $/;
const emptyOlLiRegex = /^\d+\. $/;

$textarea.on('keyup', e => {
    const $this = $(e.target);

    if (e.which === 13) {
        // `13` is the return key.
        const cursorPosition = $this.prop('selectionStart');
        const everything = $this.val();
        const beforeCursor = everything.slice(0, cursorPosition);
        const afterCursor = everything.slice(cursorPosition);
        let lines = beforeCursor.split('\n');
        const lastLine = lines[lines.length - 2];

        if (lastLine.match(ulRegex)) {
            $this.val(beforeCursor + '- ' + afterCursor);
            $this[0].setSelectionRange(cursorPosition + 2, cursorPosition + 2);
        }

        if (lastLine.match(olRegex)) {
            let nextNumber = Number(olNumberRegex.exec(lastLine)[0]) + 1;
            let numberLength = nextNumber.toString().length + 2;
            $this.val(beforeCursor + `${nextNumber}. ` + afterCursor);
            $this[0].setSelectionRange(cursorPosition + numberLength, cursorPosition + numberLength);
        }

        if (lastLine.match(emptyLiRegex)) {
            let offset = 3;

            if (lastLine.match(emptyOlLiRegex)) {
                offset += Number(olNumberRegex.exec(lastLine)[0].length);
            }

            lines.splice(-2, 1);
            $this.val(lines.join('\n') + '' + afterCursor);
            $this[0].setSelectionRange(cursorPosition - offset, cursorPosition - offset);
        }
    }
});
