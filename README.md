# xls2moodle
Script to convert multiple choice questions from xls to moodle's xml format

## input
The script requires two arguments as commandline options (see MoodleXML usage):
- course name
- location of tabular excel file with questions

## output
- xml format, ready for import in moodle

## question format

Please refer to the template_advanced.xlsx to get an ideao on the file format.
Mandatory columns:
- Aussage1 - possible answer 1
- Aussage2 - possible answer 2
- Aussage3 - possible answer 3
- Aussage4 - possible answer 4
- WAHR - contains index of correct answer(s), 1-based
- FALSCH - contains index of wrong answer(s), 1-based
- Themenblock - contains a topic name (this should be the same for similar questions)
- Hauptfrage - Question text

Optional columns:
- Anwendung - boolean, filter to include (1) or exclude (0) questions

Further columns are ignored.

## templates
The script reads templates (xml_templates-folder) that were previously exported from moodle.
If the format changes in the future this processed needs to be repeated. In the meantime, do
not touch any of the tempalte xmls.

## known issues
- latex equation code supported (?)
- reading of data with special encoding (utf-8) currently not possible with the latest pandas version
