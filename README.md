# Swift compiler "ran out of source locations" when compiling module with many module map files

This repository contains scripts that generate headers and module map files necessary to reproduce an internal compiler error when compiling a Swift module with many module map files representing Objective-C modules.

## Instructions

1. Run `./generate.py`
2. Run `./compile.sh`

## The error

```
/tmp/swift-ran-out-of-source-locations/module_maps/../headers/module_146.h:1:2: error: malformed or corrupted AST file: 'ran out of source locations'
#import "module_147.h"
 ^
/tmp/swift-ran-out-of-source-locations/module_maps/../headers/module_146.h:1:2: note: after modifying system headers, please delete the module cache at '/var/folders/…/ModuleCache/3RAH7462NC6RF'
#import "module_147.h"
 ^
Stack dump:
0.	/tmp/swift-ran-out-of-source-locations/module_maps/../headers/module_146.h:1:2: current parser token 'import'
0  swift                    0x000000010953f4ea PrintStackTraceSignalHandler(void*) + 42
1  swift                    0x000000010953ecc0 SignalHandler(int) + 352
2  libsystem_platform.dylib 0x00007fff6a2205fd _sigtramp + 29
3  libsystem_platform.dylib 0x000000010ad20a00 _sigtramp + 2695889952
4  swift                    0x00000001080c8173 clang::CompilerInstance::loadModule(clang::SourceLocation, llvm::ArrayRef<std::__1::pair<clang::IdentifierInfo*, clang::SourceLocation> >, clang::Module::NameVisibilityKind, bool) + 21539
5  swift                    0x00000001091b8b76 clang::Preprocessor::HandleHeaderIncludeOrImport(clang::SourceLocation, clang::Token&, clang::Token&, clang::SourceLocation, clang::DirectoryLookup const*, clang::FileEntry const*) + 15670
6  swift                    0x00000001091b4c45 clang::Preprocessor::HandleIncludeDirective(clang::SourceLocation, clang::Token&, clang::DirectoryLookup const*, clang::FileEntry const*) + 117
7  swift                    0x00000001091bdf21 clang::Preprocessor::HandleDirective(clang::Token&) + 9393
8  swift                    0x000000010917f151 clang::Lexer::LexTokenInternal(clang::Token&, bool) + 11841
9  swift                    0x00000001091f1962 clang::Preprocessor::Lex(clang::Token&) + 210
10 swift                    0x0000000108399d67 clang::Parser::ParseTopLevelDecl(clang::OpaquePtr<clang::DeclGroupRef>&, bool) + 487
11 swift                    0x0000000108399a6a clang::Parser::ParseFirstTopLevelDecl(clang::OpaquePtr<clang::DeclGroupRef>&) + 42
12 swift                    0x00000001082ce865 clang::ParseAST(clang::Sema&, bool, bool) + 309
13 swift                    0x0000000108123e33 clang::FrontendAction::Execute() + 291
14 swift                    0x00000001080d3920 clang::CompilerInstance::ExecuteAction(clang::FrontendAction&) + 1840
15 swift                    0x00000001080d2c80 void llvm::function_ref<void ()>::callback_fn<compileModuleImpl(clang::CompilerInstance&, clang::SourceLocation, llvm::StringRef, clang::FrontendInputFile, llvm::StringRef, llvm::StringRef, llvm::function_ref<void (clang::CompilerInstance&)>, llvm::function_ref<void (clang::CompilerInstance&)>)::$_3>(long) + 176
16 swift                    0x00000001094b7bd6 RunSafelyOnThread_Dispatch(void*) + 38
17 swift                    0x00000001095402ed ExecuteOnThread_Dispatch(void*) + 13
18 libsystem_pthread.dylib  0x00007fff6a22c109 _pthread_start + 148
19 libsystem_pthread.dylib  0x00007fff6a227b8b thread_start + 15
<unknown>:0: error: unable to execute command: Segmentation fault: 11
<unknown>:0: error: compile command failed due to signal 11 (use -v to see invocation)
```

## About the contents of this repository

`generate.py` is a Python script that creates 5,000 module map files and corresponding Objective-C headers. 150 of these headers import headers from different modules. The result is that importing
the first of these modules from Swift will cause the other 149 modules to be loaded.

`compile.sh` contains the Swift compiler invocation. It's a straight-forward invocation. The most relevant flags are the `-Xcc -fmodule-map-file=…` flags that are generated for each Objective-C module.

## Why is there a source location shortage?

The loading of a single module allocates source locations for every module map file that was passed to the compiler. When the Clang importer imports a module while processing a module, the loaded module's source locations are added to the set of source locations for the current module. This a given module can many ranges of source locations that represent the same module map files (one copy for when it loaded the module map files itself, plus one for each transitive module it depends on). If the total size of the module map files is large, this can cause the 31-bit source location limit to be hit with only a few hundred transitive module imports and several thousand module map files.

## Why on earth do you have several hundred transitive module imports and several thousand module map files?!

In short, due to integrating Swift code with a huge existing Objective-C code base.

[Bazel](https://bazel.build/) encourages use of very granular targets for Objective-C code. The overhead of adding additional Objective-C library targets is very low, and they're convenient to narrowly group code. It's not uncommon to have targets with only a one or two header and source files, and as a result a large application can easily depend on hundreds or thousands of Objective-C library targets.

In order to interoperate with Swift, each Objective-C library target is treated as a module and generates an associated module map file. Objective-C modules will only be loaded by the Swift compiler when imported, but Swift must then transitively load modules referenced via `#import`s in that module's headers in order to make type defintions available that may be used in the module's interface. This can result in a single Swift `import` bringing in tens or more Objective-C modules.

In order to establish the mappings between Objective-C headers and the modules that contain them, the module map files must be passed to the compiler.
