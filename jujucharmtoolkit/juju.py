import os
import json
import subprocess
import sys

def _run_command(args, stdin='', exit_codes=[0], **kwargs):
  print "Running command: " + ' '.join(args)

  proc = subprocess.Popen(args,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          **kwargs)

  out, err = proc.communicate(input=stdin)
  retcode = proc.returncode
  if not retcode in exit_codes:
    print "Calling return error: " + ' '.join(args)
    print "Output: " + out
    print "Error: " + err
    raise subprocess.CalledProcessError(retcode, args)
  return out, err

class Juju(object):
  _cache_config = None

  @classmethod
  def config(cls):
    if not cls._cache_config:
      stdout, _ = _run_command(['config-get', '--format', 'json'])
      cls._cache_config = json.loads(stdout)
    return cls._cache_config

  @classmethod
  def action(cls):
    """Infer the action from the process name.
    
    This probably should be passed as an env variable."""
    proc_name = os.path.basename(sys.argv[0])
    proc_name = proc_name.replace('-', '_')
    juju_action = None

    if proc_name.endswith('_joined'):
      juju_action = 'joined'
    elif proc_name.endswith('_changed'):
      juju_action = 'changed'
    elif proc_name.endswith('_broken'):
      juju_action = 'broken'

    if not juju_action:
      raise Exception("Unknown action: %s" % proc_name)

    return juju_action

  @classmethod
  def unit_name(cls):
    return os.environ["JUJU_UNIT_NAME"]

  @classmethod
  def service_name(cls):
    unit_name = cls.unit_name()
    tokens = unit_name.split('/')
    if len(tokens) > 0:
      return tokens[0]
    else:
      return ""

  @classmethod
  def env_uuid(cls):
    return os.environ['JUJU_ENV_UUID']

  @classmethod
  def get_property(cls, key):
    args = ["unit-get", "--format", "json", key]
    stdout, _ = _run_command(args)
    return json.loads(stdout)

  @classmethod
  def private_address(cls):
    v = cls.get_property('private-address')
    return str(v)

class Relation(object):
  def __init__(self, relation_id=None):
    if not relation_id:
      relation_id = os.environ['JUJU_RELATION_ID']
    self.relation_id = relation_id

  @classmethod
  def default(cls):
    return Relation()

  def set_properties(self, properties):
    args = ['relation-set']
    if self.relation_id:
      args.append("-r")
      args.append(self.relation_id)

    for k, v in properties.items():
      args.append("%s=%s" % (k, v))

    _run_command(args)

  def get_properties(self, unit_id=None):
    args = ["relation-get", "--format", "json"]
    if self.relation_id:
      args.append("-r")
      args.append(self.relation_id)
    args.append("-")  # Key
    if unit_id:
        args.append(unit_id)
    stdout, _ = _run_command(args)
    return json.loads(stdout)
