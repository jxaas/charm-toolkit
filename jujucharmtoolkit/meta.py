import os
import subprocess
import sys
import StringIO
import ConfigParser

def run_command(args, stdin='', exit_codes=[0], **kwargs):
  print 'Running command: ' + ' '.join(args)

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

def _run_apt_get_install(*pkgs):
    cmd = [
        'apt-get',
        '-y',
        'install'
          ]
    for pkg in pkgs:
        cmd.append(pkg)
    run_command(cmd)

def _run_wget(src, dest):
    # Default Python doesn't validate SSL certificates...
    # Just use wget
    cmd = [ 'wget',
            '-O', dest,
            src
          ]
    run_command(cmd)

def _expand_archive(src, dest, expand_strip_components=None, **kwargs):
    cmd = [ 'tar' ]

    cmd = cmd + [ '-C', dest ]

    if expand_strip_components:
        cmd = cmd + [ '--strip-components=' + expand_strip_components ]

    cmd = cmd + [ '-z', '-x', '-f', src ]

    run_command(cmd)

def _get_sha256(path):
    cmd = [ 'sha256sum', '--binary', path ]
    out, _ = run_command(cmd)
    tokens = out.split(" ")
    return tokens[0]

def do_download(src, dest, expand=None, sha256=None, **kwargs):
    ensure_dir(os.path.dirname(dest))

    download = True

    if sha256 and os.path.exists(dest):
        actual_sha256 = _get_sha256(dest)
        if sha256 == actual_sha256:
            download = False

    if download:
        _run_wget(src, dest)

    # We do re-run the SHA calculation (unnecessarily) when it is already downloaded
    actual_sha256 = _get_sha256(dest)

    print "actual sha256 is: %s" % actual_sha256
    if sha256 and sha256 != actual_sha256:
        print "SHA mismatch"
        raise Exception("SHA mismatch")

    if expand:
        _expand_archive(dest, expand, **kwargs)

def do_user(name):
    #     juju-log "create elasticsearch user"
    out, _ = run_command(['id', '-u', name], exit_codes=[0, 1])
    if not out:
        run_command(['useradd', name])

def _expand_template(env, src):
  out = src
  for k, v in env.iteritems():
    out = out.replace('{{' + k + '}}', v)
  return out

def do_template(env, src_file, relpath):
    dest_file = os.path.join('/', relpath)

    with open(src_file, 'r') as f:
        src = f.read()

    dest = _expand_template(env, src)

    ensure_dir(os.path.dirname(dest_file))

    # juju_log('INFO', "Writing file: %s" % dest_file)
    with open(dest_file, 'w') as f:
        f.write(dest)

def do_service_install(src_file, relpath):
    with open(src_file, 'r') as f:
        src = f.read()

    #     install -o root -g root -m 0644 ${HOME}/../files/charm/services/elasticsearch.conf /etc/init/elasticsearch.conf

    with open(os.path.join('/etc/init', relpath), 'w') as f:
        f.write(src)

def ensure_dir(path):
    if os.path.exists(path):
        return
    cmd = [ 'mkdir', '-p', path ]
    run_command(cmd)

def read_config(path):
    with open(path, 'r') as f:
        text = f.read()
    text = "[main]\n" + text
    config_stream = StringIO.StringIO(text)
    config = ConfigParser.RawConfigParser()
    config.readfp(config_stream)
    return config

def run_configs(key, fn):
    base = os.path.join('meta', key)
    for root, dirs, files in os.walk(base):
        for file in files:
            path = os.path.join(root, file)
            config = read_config(path)
            for section in config.sections():
                kwargs = {}
                kwargs['name'] = os.path.basename(path)
                for k, v in config.items(section):
                    kwargs[k] = v
                fn(**kwargs)

def run_files(key, fn):
    base = os.path.join('meta', key)
    for root, dirs, files in os.walk(base):
        for file in files:
            src = os.path.join(root, file)
            relpath = os.path.relpath(src, base)
            print "%s %s %s" % (root, dirs, file)
            fn(src, relpath)

def chown(user, dir, recursive=False):
  args = ['chown']
  if recursive:
    args.append('-R')
  args.append(user)
  args.append(dir)
  run_command(args)

