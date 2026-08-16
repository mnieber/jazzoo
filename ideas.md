Ideas:

- allow to assign any json to a variable and allow to create structured objects, e.g. 🐆.config.name = "jane".
  - substitution such as `echo 🐆.config` will convert from json to string
  - `🐆.config = 🐭.load_config() | ⚙️.parse` parses the result of `🐭.load_config()` as a json string.
- lambda functions: 🐆.foo = (name="okay") => 🐭.log(🐆.name)
- support `from hello.jaz export (build_fe as build,) as fe
  - this allows the caller to use `jaz fe.build mode=dev`
  - this works recursively, so if `fe` exports `react` then you may end up having `jaz fe.react.build mode=dev`
  - you can list an exported layer using `jaz --list fe` or `jaz --list fe.build` or show the entire tree using `jaz --list-all`
  - when you export `as fe` multiple times then it aggregates (however, collisions are an error)
  - you can both export `as fe` and import `as fe` (jazzoo keeps them separate; a jazzoo file can only refer to imported functions)
- support ⚙️.loadenv(filename)
