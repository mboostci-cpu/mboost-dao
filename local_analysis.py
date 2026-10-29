"""Offline documentary inventory. Deliberately does not issue eligibility verdicts."""
import re

def local_extract(sources,candidate):
    requirements=[];facts=[];warnings=[]
    for sid,pages in sources.items():
        for page in pages:
            text=page['text']
            if page.get('warning'):warnings.append(f"{sid}, unité {page['page']} : {page['warning']}")
            if not text.strip():warnings.append(f"{sid}, unité {page['page']} : aucune lecture exploitable")
            if sid=='S01':
                for match in list(re.finditer(r'conducteur\s+des?\s+travaux|chef\s+de\s+chantier|CV\s+devra|périodes\s+de\s+stage',text,re.I))[:12]:
                    start=max(0,text.rfind('\n',0,match.start()))
                    stop=min(len(text),match.end()+1000)
                    quote=text[start:stop].strip()
                    requirements.append({'role':'À identifier / confirmer','criterion':'Passage documentaire à qualifier manuellement','mandatory':False,'source_id':sid,'page':page['page'],'quote':quote,'validity':'à_confirmer'})
            else:
                for line in text.splitlines():
                    if re.search(r'brevet de technicien|dipl[oô]me|master professionnel|ing[eé]nieur',line,re.I) and len(line.strip())>10:
                        quote=line.strip()
                        if len(facts)<30:facts.append({'field':'mention documentaire à contrôler','value':quote,'status':'à_confirmer','source_id':sid,'page':page['page'],'quote':quote})
    return {'mode':'extraction_locale_sans_IA','dao_requirements':requirements,'candidate_facts':facts,'matches':[],
        'questions':['Confirmer les diplômes et leur spécialité après lecture visuelle.', 'Fournir les mois de début/fin, employeurs et fonctions réellement exercées.', 'Identifier les projets réellement réalisés au poste proposé et leurs justificatifs.'],
        'contradictions':warnings,'next_actions':['Contrôler les passages extraits ; aucune conformité n’est établie en mode local.', 'Configurer un fournisseur IA pour le rapprochement sémantique complet.']}
