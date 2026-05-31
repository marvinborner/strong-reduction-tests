{-# LANGUAGE RecordWildCards #-}

import Control.DeepSeq
import Control.Exception
import Control.Monad
import qualified DeBruijn.Lennart as DeBruijn
import Suite
import System.Environment
import System.Exit
import System.IO
import System.Timeout
import Util.IdInt
import Util.Impl
import Util.Syntax.Lambda

timeoutSeconds = 10

main = do
  args <- getArgs
  let testFile = case args of
        [] -> "tests"
        path : _ -> path
  raw <- readFile testFile
  let tests = zipWith parseTest [1 ..] (lines raw)
  results <- mapM runTest tests
  let passed = length (filter id results)
  putStrLn $ "passed: " ++ show passed
  putStrLn $ "fail/timeout: " ++ show (length results - passed)
  unless (and results) exitFailure

parseTest lineNo line =
  case reverse (words line) of
    expected : "-" : input : labelWords ->
      (lineNo, unwords (reverse labelWords), fromBinary input, fromBinary expected)
    _ -> error $ "bad test line " ++ show lineNo

fromBinary bits =
  case parse [] 0 bits of
    (term, "") -> term
    (_, rest) -> error $ "trailing bits: " ++ take 32 rest

parse env next bits =
  case bits of
    '0' : '0' : rest ->
      let name = IdInt next
          (body, rest') = parse (name : env) (next + 1) rest
       in (Lam name body, rest')
    '0' : '1' : rest ->
      let (func, rest') = parse env next rest
          (arg, rest'') = parse env next rest'
       in (App func arg, rest'')
    '1' : _ ->
      let ones = length (takeWhile (== '1') bits)
          rest = drop ones bits
       in case rest of
            '0' : rest' ->
              case drop (ones - 1) env of
                name : _ -> (Var name, rest')
                [] -> error "open term"
            _ -> error "unterminated variable"
    _ -> error $ "invalid BLC: " ++ take 32 bits

runTest test = and <$> mapM (`runImpl` test) impls

runImpl LambdaImpl{..} (lineNo, _label, input, expected) = do
  putStr $ "test " ++ show lineNo ++ " " ++ impl_name ++ ": "
  hFlush stdout
  outcome <-
    try $
      timeout (timeoutSeconds * 1000000) $
        evaluate $
          force $
            let actual = (impl_toLC . impl_nf . impl_fromLC) input
             in (alphaEq expected actual, actual)
  case outcome of
    Right Nothing -> do
      putStrLn "[TIME]"
      pure False
    Left err -> do
      putStrLn $ "FAIL: " ++ show (err :: SomeException)
      pure False
    Right (Just (True, _)) -> do
      putStrLn "[PASS]"
      pure True
    Right (Just (False, actual)) -> do
      putStrLn "[FAIL]"
      putStrLn $ "  got:      " ++ show actual
      putStrLn $ "  expected: " ++ show expected
      pure False

alphaEq a b = DeBruijn.toDB a == DeBruijn.toDB b
