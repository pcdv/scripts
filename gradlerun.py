"""This script allows to run a java process through Gradle, allowing to
easily compute the classpath according to transitive dependencies of the
root module.

At the moment it requires (in this order):
    - the path of a local ivy repository
    - the name of the main dependency (in "group:name:version" format)
    - the main class to run
    - optional program arguments
    - optional JVM arguments (preceded by a single '-')
    - optional Gradle arguments (preceded by a single '-')
"""
import os
import sys
import tempfile
import subprocess

def usage():
    print "Usage:\n  gradlerun.py <repo> <module> <class> [args.. [- jvmargs.. [- gradleargs..]]]"
    sys.exit(1)

def run(repo, module, main, argv):
    level = 0
    args = [[], [], []]

    for arg in argv:
        if arg == '-':
            level += 1
            if level > 2: usage()
        else:
            args[level].append(arg)
    
    run_gradle(repo, module, main, *args)

def run_gradle(repo, module, main, args, jvmArgs, gradleArgs):
    context = dict(repo=repo, module=module, main=main,
                   args="[%s]" % ", ".join('"%s"' % a for a in args),
                   jvmArgs="%s" % ", ".join('"%s"' % a for a in jvmArgs))

    script = """
    apply plugin: 'java'

    repositories {
       mavenCentral()
       ivy {
         url "%(repo)s"
       }
    }

    dependencies {
      runtime "%(module)s"
    }

    task(main, type: JavaExec) {
      classpath = sourceSets.main.runtimeClasspath
      main = "%(main)s"
      args = %(args)s
      jvmArgs %(jvmArgs)s
    }
    """ % context


    f = tempfile.NamedTemporaryFile()
    f.write(script)
    f.flush()
    #f.close()
    cmd = ["gradle", "-q", "-b", f.name, "main"]
    cmd += gradleArgs

    if '--debug' in gradleArgs:
        print cmd
        print script

    subprocess.check_call(cmd)

if __name__ == '__main__':
    if len(sys.argv) < 4: usage()
    repo, module, main = sys.argv[1:4]
    run(repo, module, main, sys.argv[4:])
