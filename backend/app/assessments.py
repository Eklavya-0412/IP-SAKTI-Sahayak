"""Versioned triage: provisional routes, never automatic regulatory approvals."""
from .retrieval import retrieve, citation
from .assistant import DISCLAIMERS

RULE_VERSION='2026.09-pilot.1'
def q(id,en,hi,mr,options):
    return {'id':id,'labels':{'en':en,'hi':hi,'mr':mr},'options':[{'value':v,'labels':{'en':a,'hi':b,'mr':c}} for v,a,b,c in options]}
YESNO=[('yes','Yes','हाँ','होय'),('no','No','नहीं','नाही'),('unknown','Not sure','निश्चित नहीं','खात्री नाही')]
FORM={
 'use':q('use','What will the product be used or advertised for?','उत्पाद का उपयोग या विज्ञापन किस लिए होगा?','उत्पादनाचा वापर किंवा जाहिरात कशासाठी असेल?',[
    ('therapeutic','Treating or preventing disease','रोग का उपचार या रोकथाम','रोगावर उपचार किंवा प्रतिबंध'),('nutrition','Food or nutritional support','भोजन या पोषण','अन्न किंवा पोषण'),('cosmetic','Cleansing or appearance','सफाई या सौंदर्य','स्वच्छता किंवा सौंदर्य'),('unknown','Not sure / mixed claims','निश्चित नहीं / मिश्रित दावे','खात्री नाही / मिश्र दावे')]),
 'reference':q('reference','Is the formula described in an authoritative AYUSH or Schedule text?','क्या सूत्र किसी प्रामाणिक AYUSH या अनुसूची ग्रंथ में वर्णित है?','सूत्र कोणत्याही अधिकृत AYUSH किंवा अनुसूची ग्रंथामध्ये वर्णिले आहे का?',YESNO),
 'exact':q('exact','Are the ingredients, proportions, and preparation method unchanged from that authoritative text?','क्या सामग्री, अनुपात और तैयारी विधि उसी प्रामाणिक ग्रंथ के अनुसार समान हैं?','घटक, प्रमाण आणि तयार करण्याची पद्धत त्या अधिकृत ग्रंथाप्रमाणेच आहेत का?',YESNO),
 'ingredients':q('ingredients','Are all medicinal ingredients either named in the authoritative text or disclosed as non-textual, non-classical materials?','क्या सभी औषधीय घटक प्रामाणिक ग्रंथ में वर्णित हैं या गैर-शास्त्रीय सामग्री के रूप में स्पष्ट रूप से वर्णित हैं?','सर्व औषधी घटक अधिकृत ग्रंथांमध्ये नमूद केलेले आहेत की अशास्त्रीय सामग्री म्हणून स्पष्टपणे नमूद केले आहेत का?',YESNO),
 'phytopharma':q('phytopharma','Is this a standardized plant fraction being developed through a phytopharmaceutical route rather than a classical text-based preparation?','क्या यह एक मानकीकृत पौध-भिन्न अंश है जो शास्त्रीय ग्रंथ-आधारित तैयारी के बजाय फाइटोफार्मास्यूटिकल मार्ग पर विकसित किया जा रहा है?','हे प्रमाणित वनस्पती अंश आहे की शास्त्रीय ग्रंथ-आधारित तयारीऐवजी फायटोफार्मास्युटिकल मार्गाने विकसित केले जात आहे?',YESNO),
 'aahara':q('aahara','Does the food follow an Ayurveda-Aahara recipe, authorised food-category basis, or separate FSSAI route?','क्या भोजन आयुर्वेद-आहार विधि, अधिकृत खाद्य श्रेणी आधार या अलग FSSAI मार्ग का अनुसरण करता है?','अन्न आयुर्वेद-आहार पद्धत, अधिकृत खाद्य श्रेणी आधार किंवा वेगळा FSSAI मार्ग अनुसरण करते आहे का?',YESNO),
 'route':q('route','How will it be administered and marketed?','इसे कैसे प्रशासित और विपणन किया जाएगा?','ते कसे प्रशासनित आणि विपणन केले जाईल?',[
    ('oral','Oral','मुख से','तोंडावाटे'),('external','External','बाहरी','बाह्य'),('other','Other / not established','अन्य / अस्पष्ट','इतर / अस्पष्ट')]),
 'origin':q('origin','What biological materials are involved and what is the dominant source?','कौन सी जैविक सामग्री शामिल है और मुख्य स्रोत क्या है?','कोणती जैविक सामग्री समाविष्ट आहे आणि मुख्य स्रोत काय आहे?',[
    ('plant','Plant','पौधे','वनस्पती'),('microbial','Microbial','सूक्ष्मजीव','सूक्ष्मजीव'),('animal','Animal','पशु','प्राणी'),('mixed','Mixed / uncertain','मिश्रित / अनिश्चित','मिश्र / अनिश्चित')]),
 'claims':q('claims','What therapeutic, nutrition, cosmetic, or disease-related claims are intended?','कौन से चिकित्सीय, पोषण, सौंदर्य या रोग-संबंधित दावे प्रस्तावित हैं?','कोणते चिकित्सीय, पोषण, सौंदर्य किंवा रोग-संबंधित दावा प्रस्तावित आहेत?',[
    ('classic','Classical AYUSH / traditional use only','केवल शास्त्रीय AYUSH / पारंपरिक उपयोग','केवळ शास्त्रीय AYUSH / पारंपरिक उपयोग'),('health','Disease-prevention or therapeutic efficacy claims','रोग-रोकथाम या चिकित्सीय प्रभाव के दावे','रोग-प्रतिबंध किंवा चिकित्सीय प्रभावाचे दावा'),('general','General wellness or daily-use promotion','सामान्य स्वास्थ्य या दैनिक उपयोग संवर्धन','सामान्य आरोग्य किंवा दैनंदिन वापर संवर्धन'),('unknown','Not clear or mixed','स्पष्ट नहीं / मिश्रित','स्पष्ट नाही / मिश्र')]),
}
ABS={
 'origin':q('origin','Were resources or associated traditional knowledge accessed from India?','क्या संसाधन या संबंधित पारंपरिक ज्ञान भारत से लिया गया?','संसाधने किंवा संबंधित पारंपरिक ज्ञान भारतातून घेतले आहे का?',YESNO),
 'entity':q('entity','Which description best fits the applicant?','आवेदक किस श्रेणी में है?','अर्जदार कोणत्या श्रेणीतील आहे?',[
    ('indian','Indian citizen / Indian-controlled entity','भारतीय नागरिक / भारतीय नियंत्रण','भारतीय नागरिक / भारतीय नियंत्रण'),('foreign','Foreign person / foreign-controlled entity','विदेशी व्यक्ति / विदेशी नियंत्रण','परदेशी व्यक्ती / परदेशी नियंत्रण'),('unknown','Control or residency unclear','नियंत्रण या निवास अस्पष्ट','नियंत्रण किंवा निवास अस्पष्ट')]),
 'purpose':q('purpose','What is the purpose of access?','प्राप्ति का उद्देश्य क्या है?','संसाधन मिळवण्याचा उद्देश काय?',[
    ('research','Research','अनुसंधान','संशोधन'),('commercial','Commercial use','व्यावसायिक उपयोग','व्यावसायिक वापर'),('both','Research and commercialisation','अनुसंधान और व्यवसाय','संशोधन आणि व्यवसाय')]),
 'transfer':q('transfer','Will research results or materials be transferred abroad?','क्या शोध परिणाम या सामग्री विदेश भेजी जाएगी?','संशोधन निष्कर्ष किंवा सामग्री परदेशात हस्तांतरित होईल का?',YESNO),
 'ip':q('ip','Is an IP application or commercialisation of IP planned?','क्या बौद्धिक संपदा आवेदन या उसका व्यवसायीकरण होगा?','बौद्धिक संपदा अर्ज किंवा व्यापारीकरण नियोजित आहे का?',YESNO),
 'cultivated':q('cultivated','Are resources cultivated, with documentary proof of origin?','क्या संसाधन उगाए गए हैं और उत्पत्ति का प्रमाण है?','संसाधने लागवडीतून मिळाली असून उत्पत्तीचा पुरावा आहे का?',YESNO),
 'tk':q('tk','Is community-associated traditional knowledge involved?','क्या समुदाय से संबंधित पारंपरिक ज्ञान शामिल है?','समुदायाशी संबंधित पारंपरिक ज्ञान वापरले आहे का?',YESNO),
}

RESULTS={
 'classical':('Classical ASU medicine route','शास्त्रीय आयुर्वेदिक औषधि मार्ग','शास्त्रीय आयुर्वेदिक औषध मार्ग','Ayurvedic drug authoritative books formula First Schedule'),
 'proprietary':('Patent-or-proprietary ASU medicine route','पेटेंट या प्रोप्राइटरी आयुर्वेदिक औषधि मार्ग','पेटंट किंवा प्रोप्रायटरी आयुर्वेदिक औषध मार्ग','patent proprietary medicine ingredients authoritative books'),
 'new_drug':('Potential non-classical / new-drug assessment','संभावित गैर-शास्त्रीय / नई औषधि मूल्यांकन','संभाव्य अशास्त्रीय / नवीन औषध मूल्यांकन','new drug safety effectiveness phytopharmaceutical'),
 'phytopharmaceutical':('Phytopharmaceutical route to investigate','फाइटोफार्मास्यूटिकल मार्ग की जाँच','फायटोफार्मास्युटिकल मार्गाचा विचार','phytopharmaceutical purified standardized fraction'),
 'aahara':('Ayurveda-Aahara route to investigate','आयुर्वेद आहार मार्ग की जाँच','आयुर्वेद आहार मार्गाचा विचार','Ayurveda Aahara food category'),
 'food':('Food / nutraceutical route to investigate','खाद्य / न्यूट्रास्यूटिकल मार्ग की जाँच','अन्न / न्यूट्रास्युटिकल मार्गाचा विचार','food nutritional supplement Ayurveda Aahara'),
 'cosmetic':('Cosmetic route to investigate','कॉस्मेटिक मार्ग की जाँच','सौंदर्यप्रसाधन मार्गाचा विचार','cosmetic cleansing beautifying appearance'),
 'uncertain':('Classification needs clarification','वर्गीकरण के लिए स्पष्टीकरण आवश्यक','वर्गीकरणासाठी स्पष्टीकरण आवश्यक','Ayurvedic medicine classification authoritative text'),
}

def validate_answers(answers,questions):
    for key,value in answers.items():
        if key not in questions or value not in {o['value'] for o in questions[key]['options']}:
            raise ValueError(f'Invalid answer for {key}')

def question_result(question,language,answers):
    return {'complete':False,'question':{'id':question['id'],'text':question['labels'][language],
        'options':[{'value':o['value'],'label':o['labels'][language]} for o in question['options']]},
        'answered':len(answers),'rule_version':RULE_VERSION}

def classify(db,answers,language='en'):
    validate_answers(answers,FORM)
    needed=['use']
    use=answers.get('use')
    if use=='therapeutic':
        needed+=['reference']
        if answers.get('reference')=='yes': needed+=['exact']
        if answers.get('reference')=='no' or answers.get('exact')=='no':
            needed+=['ingredients']
            if answers.get('ingredients')=='no': needed+=['phytopharma']
    elif use=='nutrition': needed+=['aahara']
    if use and use!='unknown': needed+=['route','origin']
    for key in needed:
        if key not in answers: return question_result(FORM[key],language,answers)
    result='uncertain'
    if use=='cosmetic': result='cosmetic'
    elif use=='nutrition': result='aahara' if answers.get('aahara')=='yes' else 'food' if answers.get('aahara')=='no' else 'uncertain'
    elif use=='therapeutic':
        if answers.get('reference')=='yes' and answers.get('exact')=='yes': result='classical'
        elif answers.get('ingredients')=='yes': result='proprietary'
        elif answers.get('ingredients')=='no': result='phytopharmaceutical' if answers.get('phytopharma')=='yes' else 'new_drug' if answers.get('phytopharma')=='no' else 'uncertain'
    if answers.get('route')=='other': result='uncertain'
    info=RESULTS[result]
    rows,_=retrieve(db,info[3],'india',limit=3)
    labels={'en':0,'hi':1,'mr':2}
    return {'complete':True,'code':result,'title':info[labels[language]],'provisional':True,'rule_version':RULE_VERSION,
        'citations':[citation(r).model_dump() for r in rows],
        'missing_facts':[key for key,value in answers.items() if value=='unknown'],
        'posture':{'regulatory':'Confirm the route, intended claims, evidence requirements and licence with the competent authority.',
          'ip':'Regulatory classification does not establish patentability. Patent-or-proprietary is a regulatory term.',
          'traditional_knowledge':'Check authoritative texts and prior art. A search pointer is not a patentability opinion.',
          'abs':'Assess biological-resource access separately using the ABS helper.'},
        'authority_to_consult':'State AYUSH licensing authority; CDSCO for potentially applicable new-drug/phytopharmaceutical routes; FSSAI for food routes, as relevant.',
        'limitations':['Triage is based on user-supplied facts. It is not a licence determination.','Review original formula, text reference, ingredients and current rules with a qualified reviewer.'],
        'disclaimer':DISCLAIMERS[language]}

def assess_abs(db,answers,language='en'):
    validate_answers(answers,ABS)
    needed=['origin','entity','purpose','transfer','ip','cultivated','tk']
    for key in needed:
        if key not in answers:return question_result(ABS[key],language,answers)
    unclear=any(v=='unknown' for v in answers.values())
    route='review' if unclear else 'nba' if answers['entity']=='foreign' or answers['transfer']=='yes' else 'nba_sbb' if answers['ip']=='yes' else 'sbb' if answers['purpose']!='research' else 'research_review'
    if answers['origin']=='no':route='origin_review'
    rows,_=retrieve(db,'biological resources access research commercial utilisation patent approval benefit sharing','india',limit=4,category='abs')
    # Only reference the actual retrieved ABS documents.
    rows=[r for r in rows if r[2].category=='abs']
    titles={'en':'ABS assessment: authority and evidence checklist','hi':'ABS मूल्यांकन: प्राधिकरण और साक्ष्य सूची','mr':'ABS मूल्यांकन: प्राधिकरण आणि पुरावा सूची'}
    return {'complete':True,'code':route,'title':titles[language],'provisional':True,'rule_version':RULE_VERSION,
        'citations':[citation(r).model_dump() for r in rows],'missing_facts':[k for k,v in answers.items() if v=='unknown'],
        'authority_to_consult':{'nba':'NBA','nba_sbb':'NBA and relevant State Biodiversity Board','sbb':'Relevant State Biodiversity Board','research_review':'NBA / State Biodiversity Board for route clarification','origin_review':'Origin-country ABS focal point and NBA where relevant','review':'NBA / State Biodiversity Board'}[route],
        'checklist':['Document applicant nationality, residency and ownership/control.','Record biological-resource origin, access dates and procurement evidence.','Identify the relevant state, purpose of access, research transfers and IP stage.','Document associated TK and community involvement.','Check each claimed exemption against current provisions and documentary conditions.'],
        'limitations':['No automatic exemption, fee calculation, approval or compliance certificate is issued.','Cultivation or traditional use alone does not establish that every ABS obligation is excluded.'],
        'disclaimer':DISCLAIMERS[language]}
