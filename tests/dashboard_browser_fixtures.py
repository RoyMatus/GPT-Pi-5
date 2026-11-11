"""Fail-safe synthetic dashboard boundary for browser scenarios outside each screen."""
def isolate_dashboard(page):
 page.route('**/api/keyboard',lambda route:route.fulfill(json={'visible':False,'height':0}))
 page.route('**/api/dashboard/**',lambda route:route.fulfill(json={
  'state':'not_configured','profile':None,'sample':None,'history':[],
  'quotes':[],'catalog':[],'watchlist':[],'selected':None,
  'files':[],'events':[],'temperature':None,'forecast':[],
  'location':{'name':'Synthetic location'},'storage':'session'}))
