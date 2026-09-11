from app.providers import source_quote

def test_pdf_whitespace_recovers_original_span():
    excerpt='Prefix. Traditional \n knowledge is not\t an invention. Suffix.'
    quote=source_quote('Traditional knowledge is not an invention.',excerpt)
    assert quote=='Traditional \n knowledge is not\t an invention.' and quote in excerpt

def test_quote_resolution_never_changes_words_or_negation():
    assert source_quote('Knowledge is an invention.','Knowledge is not an invention.') is None
    assert source_quote('Section 3(p)','Section 3(o)') is None
