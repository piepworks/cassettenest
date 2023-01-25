/* eslint-disable no-unused-vars */
const ulRegex = /^- .+/;
const olRegex = /^\d+\. .+/;
const olNumberRegex = /^\d+/;
const emptyLiRegex = /^(-|(\d+\.)) $/;
const emptyOlLiRegex = /^\d+\. $/;

const checkAutocomplete = function ($el) {
  const cursorPosition = $el.selectionStart;
  const everything = $el.value;
  const beforeCursor = everything.slice(0, cursorPosition);
  const afterCursor = everything.slice(cursorPosition);
  let lines = beforeCursor.split('\n');
  const lastLine = lines[lines.length - 2];

  if (lastLine.match(ulRegex)) {
    $el.value = `${beforeCursor}- ${afterCursor}`;
    $el.setSelectionRange(cursorPosition + 2, cursorPosition + 2);
  }

  if (lastLine.match(olRegex)) {
    let nextNumber = Number(olNumberRegex.exec(lastLine)[0]) + 1;
    let numberLength = nextNumber.toString().length + 2;
    $el.value = `${beforeCursor}${nextNumber}. ${afterCursor}`;
    $el.setSelectionRange(cursorPosition + numberLength, cursorPosition + numberLength);
  }

  if (lastLine.match(emptyLiRegex)) {
    let offset = 3;

    if (lastLine.match(emptyOlLiRegex)) {
      offset += Number(olNumberRegex.exec(lastLine)[0].length);
    }

    lines.splice(-2, 1);
    $el.value = lines.join('\n') + '' + afterCursor;
    $el.setSelectionRange(cursorPosition - offset, cursorPosition - offset);
  }
};
