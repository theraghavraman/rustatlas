// All visualizations are explicitly pedagogical models, never a compiler.
const box=(name,value,kind='valid',caption='')=>({name,value,kind,caption});
export const LABS=[
 {id:'ownership',symbol:'↗',title:'Ownership & moves',label:'Follow a value as ownership changes',source:['What Is Ownership','Understanding Ownership'],
  objective:'Distinguish moving a String from cloning and copying.',
  code:'let s1 = String::from("hello");\nlet s2 = s1; // String moves, no implicit deep clone\nprintln!("{s2}");',
  states:[
   {step:'A value has one owner',operation:'Create String',explain:'s1 owns a heap-allocated String value. Its bytes live separately from the stack binding.',nodes:[box('s1','String("hello")','focus','owner'),box('heap','h · e · l · l · o','valid','String bytes')]},
   {step:'Moving transfers ownership',operation:'Move to s2',explain:'Assigning a String to s2 moves ownership. The program must not use s1 afterwards. This is not copying the heap bytes.',nodes:[box('s1','moved','invalid','cannot use'),box('→','ownership','arrow'),box('s2','String("hello")','focus','new owner')]},
   {step:'A moved binding is rejected',operation:'Try using s1',explain:'Using s1 after the move would fail to compile. This display is a conceptual rule demonstration, not an actual compiler run.',nodes:[box('s1','unusable','invalid','compile-time restriction'),box('s2','"hello"','valid','usable')]},
   {step:'Clone is an explicit alternative',operation:'New example: clone()',explain:'In a separate example, let s2 = s1.clone() copies the String data. Both bindings then remain usable. i32 and other Copy types behave differently.',nodes:[box('s1','"hello"','valid','still usable'),box('s2','"hello"','valid','independent clone')]}
  ]},
 {id:'borrowing',symbol:'&',title:'Borrowing & references',label:'See shared versus exclusive access',source:['References and Borrowing','What Is Ownership'],
  objective:'Visualize the rule of many shared references OR an exclusive mutable reference.',
  code:'let mut s = String::from("hello");\nlet a = &s;\nlet b = &s;\nprintln!("{a} {b}");',
  states:[
   {step:'One owned value',operation:'Create String',explain:'s owns the String; no reference is active yet.',nodes:[box('s','String','focus','owner')]},
   {step:'Shared references',operation:'Borrow immutably',explain:'Multiple shared (&String) references can read the value at the same time.',nodes:[box('s','String','valid','owner'),box('a','&s','focus','shared borrow'),box('b','&s','focus','shared borrow')]},
   {step:'Exclusive mutation when allowed',operation:'End shared use; borrow mutably',explain:'After shared references are no longer used, an exclusive &mut borrow may be created in a suitable scope.',nodes:[box('s','String','valid','owner'),box('m','&mut s','focus','exclusive borrow')]},
   {step:'Conflicting active borrows',operation:'Try concurrent shared and mutable',explain:'Rust rejects an overlapping conflicting borrow. Precise borrow lifetimes are based on usage, not simply lexical blocks.',nodes:[box('a','&s','valid','active shared'),box('m','&mut s','invalid','conflicting borrow')]}
  ]},
 {id:'memory',symbol:'▥',title:'Stack, heap & slices',label:'Understand a selected memory model',source:['What Is Ownership','The Slice Type'],
  objective:'Relate an owned String, its bytes and a borrowed slice in a simplified memory view.',
  code:'let s = String::from("rust");\nlet head = &s[0..2]; // valid UTF-8 boundaries',
  states:[
   {step:'Stack metadata',operation:'Create String',explain:'A String value contains metadata (pointer, length and capacity) that references an allocation. This is a model, not an ABI guarantee.',nodes:[box('stack','ptr · len · cap','focus','String metadata')]},
   {step:'Heap allocation',operation:'Inspect bytes',explain:'The separately allocated buffer contains UTF-8 bytes: r u s t.',nodes:[box('stack','ptr →','valid','String'),box('heap','72 75 73 74','focus','UTF-8 bytes hex')]},
   {step:'Borrowed slice',operation:'Take &s[0..2]',explain:'The slice refers to the first two bytes, “ru”. String slice ranges must start and end at valid UTF-8 character boundaries.',nodes:[box('String','rust','valid','owner'),box('&str','ru','focus','borrowed view')]}
  ]},
 {id:'lifetimes',symbol:'⌛',title:'Lifetimes & scopes',label:'Track borrowed data through scopes',source:['Validating References with Lifetimes','References and Borrowing'],
  objective:'Understand why a reference may not outlive its referent.',
  code:'let r;\n{\n    let x = 5;\n    r = &x;\n}\n// using r here would be invalid',
  states:[
   {step:'Outer scope begins',operation:'Declare r',explain:'The binding r exists in the outer scope but has no referent yet.',nodes:[box('outer scope','r: uninitialized','focus')]},
   {step:'Inner scope exists',operation:'Create x and &x',explain:'x is alive inside the inner scope. A reference to it can be used while its referent is valid.',nodes:[box('inner x','5','valid','local value'),box('r','&x','focus','borrow')]},
   {step:'Scope closes',operation:'Drop x',explain:'x is dropped at the end of its scope. Returning to the outer scope with a usable reference to x would violate borrow checking.',nodes:[box('x','out of scope','invalid'),box('r','dangling if used','invalid')]},
   {step:'Annotations describe relationships',operation:'Interpret lifetimes',explain:'Lifetime annotations describe constraints between borrowed values; they never prolong an allocation by themselves.',nodes:[box("'a",'relationship','focus','annotation'),box('allocation','unchanged','valid','not extended')]}
  ]},
 {id:'match',symbol:'◇',title:'Enums & pattern matching',label:'See which match arm executes',source:['The match Control Flow Construct','Defining an Enum'],
  objective:'Map an enum value to a matching arm and explain exhaustiveness.',
  code:'enum Coin { Penny, Nickel, Dime }\nlet c = Coin::Dime;\nlet cents = match c {\n    Coin::Penny => 1,\n    Coin::Nickel => 5,\n    Coin::Dime => 10,\n};',
  states:[
   {step:'The input is a variant',operation:'Set value: Penny',explain:'Coin::Penny selects the Penny pattern and produces 1.',nodes:[box('input','Penny','focus'),box('matched arm','Penny → 1','valid')]},
   {step:'Select Nickel',operation:'Change variant',explain:'Coin::Nickel matches the second arm, producing 5.',nodes:[box('input','Nickel','focus'),box('matched arm','Nickel → 5','valid')]},
   {step:'Select Dime',operation:'Change variant',explain:'Coin::Dime matches the third arm, producing 10.',nodes:[box('input','Dime','focus'),box('matched arm','Dime → 10','valid')]},
   {step:'Every case must be covered',operation:'Check exhaustiveness',explain:'The three-variant enum can be matched exhaustively by these three arms. Omitting one without a catch-all leads to a non-exhaustive match error.',nodes:[box('Penny','covered','valid'),box('Nickel','covered','valid'),box('Dime','covered','valid')]}
  ]},
 {id:'iterator',symbol:'≋',title:'Iterators & closures',label:'Make lazy pipelines visible',source:['Processing a Series of Items with Iterators','Comparing Performance'],
  objective:'Understand how map and filter are lazy until an iterator is consumed.',
  code:'let result: Vec<_> = [1, 2, 3, 4].into_iter()\n    .map(|x| x * 2)\n    .filter(|x| x > &4)\n    .collect();',
  states:[
   {step:'Source collection',operation:'Construct iterator',explain:'Creating an iterator chain is lazy: no mapped result is produced until the chain is consumed.',nodes:[box('input','1 · 2 · 3 · 4','focus')]},
   {step:'Transform elements',operation:'Evaluate map on consumption',explain:'When collect consumes the iterator, map doubles each item: 2, 4, 6, 8.',nodes:[box('map ×2','2 · 4 · 6 · 8','focus')]},
   {step:'Select matching elements',operation:'Apply filter',explain:'Only items greater than 4 pass the predicate: 6 and 8.',nodes:[box('filter >4','6 · 8','focus')]},
   {step:'Materialize the result',operation:'Collect',explain:'collect() gathers yielded items into a Vec. This step-wise depiction summarizes lazy evaluation; the actual pipeline processes items as it iterates.',nodes:[box('Vec<i32>','[6, 8]','valid')]}
  ]},
 {id:'traits',symbol:'⚙',title:'Traits & generics',label:'Explore capabilities and bounds',source:['Traits: Defining Shared Behavior','Generic Data Types'],
  objective:'See that trait bounds constrain which concrete types are valid.',
  code:'fn show<T: std::fmt::Display>(x: T) {\n    println!("{x}");\n}',
  states:[
   {step:'Define a contract',operation:'Require Display',explain:'T: Display states the function accepts types implementing std::fmt::Display.',nodes:[box('generic T','Display required','focus')]},
   {step:'Type satisfying bound',operation:'Pass String',explain:'String implements Display, so show(String::from("hi")) satisfies the bound.',nodes:[box('String','Display ✓','valid'),box('show<T>','accepted','focus')]},
   {step:'Another valid type',operation:'Pass i32',explain:'i32 also implements Display, so the same generic function can accept it.',nodes:[box('i32','Display ✓','valid'),box('show<T>','accepted','focus')]},
   {step:'Missing implementation',operation:'Pass a type lacking Display',explain:'A custom struct that does not implement Display cannot be passed. This is a conceptual example.',nodes:[box('MyStruct','no Display','invalid'),box('show<T>','bound unsatisfied','invalid')]}
  ]},
 {id:'result',symbol:'⑂',title:'Result & error flow',label:'Trace success and failure paths',source:['Recoverable Errors with Result','Error Handling'],
  objective:'Recognize success, recoverable errors, and the effect of the ? operator.',
  code:'fn read(path: &str) -> std::io::Result<String> {\n    std::fs::read_to_string(path)\n}',
  states:[
   {step:'A fallible operation',operation:'Read a file',explain:'read_to_string returns a Result that distinguishes Ok(data) and Err(error).',nodes:[box('read_to_string','Result<String, Error>','focus')]},
   {step:'Success path',operation:'File exists',explain:'On success, Ok(text) contains the read file contents.',nodes:[box('Ok','String data','valid')]},
   {step:'Recoverable failure',operation:'File missing',explain:'The function returns Err(io::Error); the caller can decide how to handle it.',nodes:[box('Err','io::Error','invalid','recoverable')]},
   {step:'Propagation with ?',operation:'Use the ? operator',explain:'The ? operator returns early on Err and unwraps Ok in compatible Result-returning functions; it is not exception catching.',nodes:[box('Ok','continue','valid'),box('Err','return early','focus')]}
  ]},
 {id:'modules',symbol:'▣',title:'Crates & modules',label:'Inspect a small project tree',source:['Defining Modules to Control Scope and Privacy','Packages and Crates'],
  objective:'Understand that files, modules, crates, and packages are related but distinct concepts.',
  code:'// src/lib.rs\nmod garden;\npub fn plant() { garden::grow(); }\n// src/garden.rs\npub fn grow() {}',
  states:[
   {step:'Package',operation:'Open package',explain:'A Cargo package has a manifest and can contain targets such as a library or binary.',nodes:[box('Cargo.toml','package manifest','focus'),box('src/','source tree','valid')]},
   {step:'Crate root',operation:'Open lib.rs',explain:'A library crate root defines the top-level module tree for that crate.',nodes:[box('lib.rs','crate root','focus')]},
   {step:'Module definition',operation:'Declare mod garden',explain:'mod garden introduces a module whose source can be in garden.rs under a compatible project layout.',nodes:[box('lib.rs','mod garden','valid'),box('garden.rs','module source','focus')]},
   {step:'Visibility',operation:'Inspect pub fn',explain:'pub marks an item publicly accessible subject to privacy of its ancestor modules.',nodes:[box('garden::grow','pub fn','focus'),box('garden module','private here','valid')]}
  ]},
 {id:'concurrency',symbol:'⇄',title:'Threads & synchronization',label:'Compare possible interleavings',source:['Using Threads to Run Code Simultaneously','Shared-State Concurrency'],
  objective:'See that scheduling is not deterministic and shared mutation requires coordination.',
  code:'use std::thread;\nlet h = thread::spawn(|| println!("worker"));\nprintln!("main");\nh.join().unwrap();',
  states:[
   {step:'Create a worker',operation:'spawn()',explain:'spawn starts work on a new thread; the main thread continues executing.',nodes:[box('main','running','focus'),box('worker','ready','valid')]},
   {step:'One possible schedule',operation:'Main prints first',explain:'The main thread might print before the worker. This example does not guarantee that order.',nodes:[box('main','print main','focus'),box('worker','pending','valid')]},
   {step:'Another possible schedule',operation:'Worker prints first',explain:'The worker could instead run earlier. This is a distinct possible schedule.',nodes:[box('worker','print worker','focus'),box('main','pending','valid')]},
   {step:'Wait for completion',operation:'join()',explain:'join waits for the worker to finish. Shared mutable state generally needs synchronization mechanisms and correct ownership.',nodes:[box('main','joined','valid'),box('worker','completed','valid')]}
  ]}
];
export function renderLabNodes(nodes){return nodes.map((n,i)=>n.kind==='arrow'?`<div class="memory-arrow" aria-hidden="true">→</div>`:
 `<div class="memory-object ${n.kind||''}" role="group" aria-label="${esc(n.name)}: ${esc(n.value)}"><strong>${esc(n.name)}</strong><div>${esc(n.value)}</div>${n.caption?`<span>${esc(n.caption)}</span>`:''}</div>`).join('')}
export function esc(x){return String(x ?? '').replace(/[&<>"']/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]))}
