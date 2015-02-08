from pyflare import PyflareClient
import mcstatus, yaml, threading

with open('config.yml', 'r') as cfg_file:
    config = yaml.load(cfg_file)

email = config['email']
api_key = config['api-key']
domain = config['domain']
ip_pool = config['ips']
entry = config['entry']

cf = PyflareClient(email, api_key)

def get_slp_results(ips):
    results = {}
    for ip in ips:
        status = mcstatus.McServer(ip, '25565')
        status.Update()
        results[ip] = status.available
    return results

def get_records_for_name(name):
    records = {}
    response = cf.rec_load_all(domain)
    for entry in response:
        entry_name = entry['name']
        if entry_name == name:
            records[str(entry['display_content'])] = str(entry['rec_id'])
    return records

def update_entries_with_available(records, results):
    if len(results) == 0:
        return
    for ip in results.keys():
        if results[ip]:
            if ip not in records:
                print 'Adding ' + ip + ' to entries'
                cf.rec_new(domain, 'A', entry.split(".")[0], ip)
        else:
            if ip in records:
                print 'Removing ' + ip + ' from entries (id ' + records[ip] +')'
                cf.rec_delete(domain, records[ip])
    for ip in records.keys():
        if ip not in results:
            print 'Removing obselete IP ' + ip + ' from entries (id ' + records[ip] +')'
            cf.rec_delete(domain, records[ip])

def schedule_update():
    print 'Running periodic update task'
    threading.Timer(45, schedule_update).start()
    slp_results = get_slp_results(ip_pool)
    cf_records = get_records_for_name(entry)
    update_entries_with_available(cf_records, slp_results)

try:
    schedule_update()
except KeyboardInterrupt:
    sys.exit(0)

