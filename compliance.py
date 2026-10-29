"""Conservative checks: dates must be supplied; never infer a career."""
from datetime import date

def relevant_months(periods, cutoff):
    """Union of full calendar months, excluding internships and future work."""
    end_limit=date.fromisoformat(cutoff)
    months=set()
    for item in periods:
        if item.get('internship') or item.get('status') not in ('prouvé','confirmé_par_candidat'):
            continue
        start=date.fromisoformat(item['from'])
        end=min(date.fromisoformat(item['to']),end_limit)
        if end<start: raise ValueError('Période inversée')
        # Full months only. A month is counted once even for concurrent jobs.
        cursor=start.year*12+start.month-1
        if start.day>1: cursor+=1
        stop=end.year*12+end.month-1
        for index in range(cursor,stop): months.add(index)
    return len(months)

def missing_personnel_documents(person):
    required=('signed_cv','diploma_certified_copy','identity_document')
    return [key for key in required if not person.get(key)]
